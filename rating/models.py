from django.db import models


class Movie(models.Model):
    uid = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    img = models.CharField(max_length=100)
    day = models.DateField()
    rating = models.IntegerField()
    comment = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)
    intro = models.CharField(max_length=20)

    def __str__(self):
        return self.title


class User(models.Model):
    uid = models.CharField(max_length=20)
    update_time = models.DateTimeField()

    def __str__(self):
        return "{}:{}".format(self.uid, self.update_time)

