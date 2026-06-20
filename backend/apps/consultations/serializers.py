from rest_framework import serializers
from .models import Consultation, Quote


class QuoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Quote
        fields = ['id', 'consultation_id', 'supplier_id', 'supplier_name',
                  'unit_price', 'delay_days', 'available', 'quality_score', 'selected']


class ConsultationSerializer(serializers.ModelSerializer):
    supplier_ids = serializers.PrimaryKeyRelatedField(source='suppliers', many=True, read_only=True)
    article_ids = serializers.PrimaryKeyRelatedField(source='articles', many=True, read_only=True)
    quotes = QuoteSerializer(many=True, read_only=True)

    class Meta:
        model = Consultation
        fields = ['id', 'code', 'request_id', 'supplier_ids', 'article_ids', 'status', 'created_at', 'quotes']


class ConsultationCreateSerializer(serializers.ModelSerializer):
    supplier_ids = serializers.PrimaryKeyRelatedField(
        source='suppliers', many=True,
        queryset=__import__('apps.suppliers.models', fromlist=['Supplier']).Supplier.objects.all()
    )
    article_ids = serializers.PrimaryKeyRelatedField(
        source='articles', many=True,
        queryset=__import__('apps.articles.models', fromlist=['Article']).Article.objects.all()
    )

    class Meta:
        model = Consultation
        fields = ['request', 'supplier_ids', 'article_ids']

    def create(self, validated_data):
        suppliers = validated_data.pop('suppliers', [])
        articles = validated_data.pop('articles', [])
        c = Consultation.objects.create(**validated_data)
        c.suppliers.set(suppliers)
        c.articles.set(articles)
        return c
