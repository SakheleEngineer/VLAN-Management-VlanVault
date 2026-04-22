

from django.db import models

class History(models.Model):
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    vlan = models.PositiveIntegerField()
    customer = models.CharField(max_length=100)
    nameUpdateBy = models.CharField(max_length=200)
    usage = models.CharField(max_length=20)
    service = models.CharField(max_length=50)


    def __str__(self):
        return f"{self.action} - {self.created_at}"

