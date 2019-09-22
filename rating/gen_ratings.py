import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime


class DoubanRating:
    def __init__(self):
        self.start_link = 'https://movie.douban.com/people/162495312/collect?start='
        self.depth = 6

    def generate_info(self):
        info = []
        for i in range(self.depth):
            link = self.start_link + str(15 * i)
            info.append(self.get_rating_list(link))
        return info

    def get_rating_list(self, link):
        doc = requests.get(link)
        doc.encoding = 'utf-8'
        soup = BeautifulSoup(doc.text)
        items = soup.find_all(class_='item')
        for item in items:
            title = item.find('em')
            comment = item.find(class_='comment')
            if title is None or comment is None:
                continue
            title = title.string
            if " /" in title:
                title = title.split(" /")[0]
            img = item.find('img')
            if img is not None:
                img = img['src']
            else:
                img = ""
            rating = item.find(class_=re.compile(r"rating"))
            if rating is not None:
                rating = rating['class'][0]
                rating = int(rating[rating.find("-") - 1])
            else:
                rating = 0
            day = item.find(class_='date')
            if day is None:
                now = datetime.now()
                day = datetime(now.year, now.month, 1)
            else:
                day = datetime.strptime(day.string, '%Y-%m-%d')
            return {"img": img, "title": title, "rating": rating, "comment": comment.string, "day": day}
