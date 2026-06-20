from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from .models import StockMovement
from apps.articles.models import Article
from apps.articles.serializers import ArticleSerializer


class StockMovementSerializer(serializers.ModelSerializer):
    article_name = serializers.CharField(source='article.name', read_only=True)
    type = serializers.CharField(source='movement_type')

    class Meta:
        model = StockMovement
        fields = ['id', 'article_id', 'article_name', 'type', 'quantity', 'reference', 'at']


class MovementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = StockMovement.objects.select_related('article').all()
        article_id = request.query_params.get('article_id')
        if article_id:
            qs = qs.filter(article_id=article_id)
        return Response(StockMovementSerializer(qs, many=True).data)


class StockAlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import F
        articles = Article.objects.filter(current_stock__lt=F('min_threshold'))
        return Response(ArticleSerializer(articles, many=True).data)
