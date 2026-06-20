from rest_framework import serializers
from .models import Article, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_ids = serializers.PrimaryKeyRelatedField(
        source='suppliers', many=True, read_only=True
    )

    class Meta:
        model = Article
        fields = ['id', 'reference', 'name', 'unit', 'category_id', 'category_name',
                  'min_threshold', 'current_stock', 'safety_stock', 'supplier_ids']


class ArticleWriteSerializer(serializers.ModelSerializer):
    supplier_ids = serializers.PrimaryKeyRelatedField(
        source='suppliers', many=True, queryset=__import__('apps.suppliers.models', fromlist=['Supplier']).Supplier.objects.all(),
        required=False
    )

    class Meta:
        model = Article
        fields = ['reference', 'name', 'unit', 'category', 'min_threshold',
                  'current_stock', 'safety_stock', 'supplier_ids']

    def create(self, validated_data):
        suppliers = validated_data.pop('suppliers', [])
        article = Article.objects.create(**validated_data)
        article.suppliers.set(suppliers)
        return article

    def update(self, instance, validated_data):
        suppliers = validated_data.pop('suppliers', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if suppliers is not None:
            instance.suppliers.set(suppliers)
        return instance
