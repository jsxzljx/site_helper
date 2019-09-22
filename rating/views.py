# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.db import models
from rating.models import Movie, User

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, date, timedelta
import os

class Updater:
    def __init__(self):
        self.link_templ = 'https://movie.douban.com/people/{}/collect?start='
        self.img_dir = "imgs"
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)

    def init_uid(self, uid):
        # flush the db
        info = self.__get_info(uid, depth=50, is_update=False)
        self.__update_db(uid, info)

    def update_uid(self, uid):
        # update the db
        info = self.__get_info(uid, depth=50, is_update=True)
        self.__update_db(uid, info)

    def __update_db(self, uid, info):
        if len(info) == 0:
            print("info is empty")
            return
        for i in info:
            # use (uid, title, img, day) as query key, as to this query,
            # if found results, update theme for values in "defaults" dict
            # if no results, insert a new record whose values are query key + values in "defaults"
            Movie.objects.update_or_create(
                uid=uid,
                title=i["title"],
                day=i["day"],

                defaults={"comment": i["comment"], "rating": i["rating"],
                          "img": i["img"].split('/')[-1], "url": i["url"], "intro": i["intro"]}
            )

        img_urls = [i["img"] for i in info]
        self.__save_imgs(img_urls)
        print("[update db] successfully init/update {} records for uid={}".format(len(info), uid))

    def __save_imgs(self, img_urls):
        for img_url in img_urls:
            img_save_path = os.path.join(self.img_dir, img_url.split('/')[-1])
            if not os.path.exists(img_save_path):
                with open(img_save_path, 'wb') as file:
                    html = requests.get(img_url)
                    if html.status_code == 200:
                        file.write(html.content)
                        file.flush()

    def __get_info(self, uid, depth=50, is_update=True):
        info = []
        need_update = True
        for i in range(depth):
            if not need_update:
                break
            link = self.link_templ.format(uid) + str(15 * i)
            res = self.__get_rating_list(link)
            print("[get info] depth={}, res length={}".format(i, len(res)))
            if len(res) == 0:
                break
            if is_update:
                for i in res:
                    if Movie.objects.filter(uid=uid, title=i["title"], day=i["day"]).exists():
                        need_update = False
                        break
            info.extend(res)
        return info

    def __get_rating_list(self, link):
        doc = requests.get(link)
        doc.encoding = 'utf-8'
        soup = BeautifulSoup(doc.text, features="lxml")
        items = soup.find_all(class_='item')
        res = []
        for item in items:
            title = item.find('em')
            comment = item.find(class_='comment')
            if title is None or comment is None:
                continue
            title = title.string
            if " /" in title:
                title = title.split(" /")[0]
            url = item.find(class_="title")
            url = url.a["href"] if url else ""
            intro = item.find(class_="intro")
            intro = intro.string.split("-")[0] if intro else "Unknown"
            img = item.find('img')
            img = img['src'] if img else ""
            rating = item.find(class_=re.compile(r"rating"))
            if rating:
                rating = rating['class'][0]
                rating = int(rating[rating.find("-") - 1])
            else:
                rating = 0
            day = item.find(class_='date')
            if day is None:
                now = datetime.now()
                day = date(now.year, now.month, 1)
            else:
                day = date(*map(int, day.string.split('-')))
            res.append({
                "title": title, "img": img, "day": day, "rating": rating,
                "comment": comment.string, "url": url, "intro": intro})
        return res


updater = Updater()


def get(request):
    uid = request.GET.get('uid', "162495312")
    start = int(request.GET.get('start', 0))
    len = int(request.GET.get('len', 12))
    if not User.objects.filter(uid=uid).exists():
        updater.init_uid(uid)
        User.objects.update_or_create(uid=uid, defaults={"update_time": datetime.now(tz=timezone.utc)})

    update_time = User.objects.get(uid=uid).update_time
    if update_time and update_time < datetime.now(tz=timezone.utc) - timedelta(days=1):
        # update the db every 1 day
        updater.update_uid(uid)
    info = []
    for item in Movie.objects.filter(uid=uid).order_by('-day')[start:start + len]:
        info.append({
            "title": item.title,
            "img": item.img,
            "day": item.day.strftime("%Y/%m/%d"),
            "rating": "⭐" * item.rating,
            "comment": item.comment,
            "url": item.url,
            "intro": item.intro,
        })
    return render(request, 'index.html', {"info": info})



