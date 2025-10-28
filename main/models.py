from django.db import models

# Create your models here.
class Users(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    gender = models.CharField(max_length=100)
    height = models.IntegerField()
    activity_level = models.IntegerField()
    role = models.CharField(max_length=20)
    table_id = models.IntegerField(db_default=None, null=True)

