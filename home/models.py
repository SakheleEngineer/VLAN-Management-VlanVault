from django.db import models

class VlanActivity(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARN', 'Warning'),
        ('ERROR', 'Error'),
    ]

    vlan_id = models.PositiveIntegerField()
    message = models.TextField()
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='INFO')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] VLAN {self.vlan_id}: {self.message}"

