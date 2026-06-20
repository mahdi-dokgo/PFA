from rest_framework import serializers
from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_name', 'email', 'phone',
                  'specialty', 'avg_lead_time_days', 'status', 'notes']
