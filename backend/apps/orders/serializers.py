from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import services
from .models import PurchaseOrder, POLine


class POLineSerializer(serializers.ModelSerializer):
    article_name = serializers.CharField(source='article.name', read_only=True)

    class Meta:
        model = POLine
        fields = ['id', 'article_id', 'article_name', 'quantity', 'unit_price', 'received_quantity']


class POLineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = POLine
        fields = ['article', 'quantity', 'unit_price']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_id = serializers.IntegerField(source='supplier.id', read_only=True)
    request_id = serializers.IntegerField(source='request.id', read_only=True, allow_null=True)
    lines = POLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'code', 'supplier_id', 'supplier_name', 'request_id',
                  'status', 'expected_date', 'total_amount', 'created_at', 'lines']


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    lines = POLineWriteSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'request', 'expected_date', 'total_amount', 'lines']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        try:
            return services.create_purchase_order_with_lines(
                supplier=validated_data['supplier'],
                request=validated_data.get('request'),
                expected_date=validated_data['expected_date'],
                total_amount=validated_data.get('total_amount', 0),
                lines_data=lines_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'request': exc.messages})
