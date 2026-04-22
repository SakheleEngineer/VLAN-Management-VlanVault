from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    datacenter = models.ForeignKey(
        "data_center.DataCenter",
        on_delete=models.PROTECT,
        related_name="regions",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name