from rest_framework import serializers
from .models import Reception, ReceptionLine


class ReceptionLineSerializer(serializers.ModelSerializer):
    article_name = serializers.CharField(source='article.name', read_only=True)

    class Meta:
        model = ReceptionLine
        fields = ['id', 'po_line_id', 'article_id', 'article_name', 'ordered_quantity', 'received_quantity']


class ReceptionSerializer(serializers.ModelSerializer):
    po_code = serializers.CharField(source='po.code', read_only=True)
    lines = ReceptionLineSerializer(many=True, read_only=True)

    class Meta:
        model = Reception
        fields = ['id', 'code', 'po_id', 'po_code', 'received_at', 'receiver_name', 'notes', 'lines']


class ReceptionLineWriteSerializer(serializers.Serializer):
    po_line_id = serializers.IntegerField()
    article_id = serializers.IntegerField()
    article_name = serializers.CharField()
    ordered_quantity = serializers.IntegerField()
    received_quantity = serializers.IntegerField()


class ReceptionCreateSerializer(serializers.Serializer):
    po_id = serializers.IntegerField()
    po_code = serializers.CharField()
    receiver_name = serializers.CharField()
    notes = serializers.CharField(required=False, default='')
    lines = ReceptionLineWriteSerializer(many=True)
