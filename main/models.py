from django.db import models

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


class Tables(models.Model):
    height = models.IntegerField()
    api_key = models.CharField()
    

class UserTablePairs(models.Model):
    user_id = models.IntegerField()
    @classmethod
    def add_pair(cls, id, user_id):
        table = cls.objects.create(id=id,user_id=user_id)
        return table

class PositionChanges(models.Model):
    user_id = models.IntegerField()
    position_change_time = models.DateTimeField()

class Statistics(models.Model):
    user_id = models.IntegerField()
    standing_time = models.IntegerField()
    sitting_time = models.IntegerField()
    position_changs = models.IntegerField()  
    date = models.DateTimeField()

