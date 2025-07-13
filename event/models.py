from django.db import models


# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=200)
    tag = models.CharField(max_length=200)
    link = models.URLField()
    time = models.DateTimeField()
    is_active = models.BooleanField()

    class Meta:
        managed = False
