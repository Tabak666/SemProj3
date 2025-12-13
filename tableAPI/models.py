from django.db import models

class Desk(models.Model):
    name = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=17, blank=True, null=True, unique=True)
    room = models.CharField(max_length=50, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Desk'
        verbose_name_plural = 'Desks'

    def __str__(self):
        return f"{self.name} ({self.id})"
