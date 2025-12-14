from django.db import models
from django.contrib.auth.hashers import make_password
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
]

class Users(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES)
    height = models.IntegerField()
    activity_level = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=20, default='user')
    approved = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

class UserTablePairs(models.Model):
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    desk_id = models.CharField(max_length=50, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id.username} → {self.desk_id} (Active: {self.end_time is None})"
class PasswordResetRequest(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    new_password = models.CharField(max_length=100)  # Store hashed password
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)  # To mark as handled
    
    class Meta:
        ordering = ['-requested_at']
        
class BugReport(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    desk_id = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Bug #{self.id} - {self.title}"
class DeskBooking(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    desk_id = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} booked {self.desk_id} from {self.start_time} to {self.end_time}"
