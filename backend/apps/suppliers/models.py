from django.db import models


class Supplier(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        ARCHIVED = 'archived', 'Archivé'

    name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    specialty = models.CharField(max_length=200, blank=True)
    avg_lead_time_days = models.PositiveIntegerField(default=7)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
