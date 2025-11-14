from django.db import models

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
]

class Users(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES)
    height = models.IntegerField()
    activity_level = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=20, default='user')
    approved = models.BooleanField(default=False)

class UserTablePairs(models.Model):
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    desk_id = models.CharField(max_length=50, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id.username} → {self.desk_id} (Active: {self.end_time is None})"
