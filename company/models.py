from django.db import models


from django.db import models


class Company(models.Model):
    # Core details
    name = models.CharField(max_length=150, unique=True)
    is_customer = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)
    # Address fields
    street = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=2, default="ZA")

    # Metadata
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


from django.db import models


from django.db import models


class Company(models.Model):
    # Core details
    name = models.CharField(max_length=150, unique=True)

    street = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=2, default="ZA")
    code = models.CharField(max_length=50, blank=True, null=True)
    companytype = models.CharField(max_length=255, blank=True, null=True)

    # Metadata
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name



class ENNI(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="ennis"
    )
    so_number = models.CharField(max_length=150)
    description = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.code} - {self.company.name}"



