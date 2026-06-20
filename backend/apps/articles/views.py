from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import Article, Category
from .serializers import ArticleSerializer, ArticleWriteSerializer, CategorySerializer
from apps.common.permissions import IsAdminOrAcheteur, IsAdminOrAcheteurReadAll


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrAcheteurReadAll]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    # GET : tout rôle authentifié ; PUT/PATCH/DELETE : ADMIN ou ACHETEUR
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrAcheteurReadAll]


class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.select_related('category').prefetch_related('suppliers').all()
    permission_classes = [IsAdminOrAcheteurReadAll]

    def get_serializer_class(self):
        return ArticleWriteSerializer if self.request.method == 'POST' else ArticleSerializer

    def create(self, request, *args, **kwargs):
        serializer = ArticleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_201_CREATED)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.select_related('category').prefetch_related('suppliers').all()
    permission_classes = [IsAdminOrAcheteurReadAll]

    def get_serializer_class(self):
        return ArticleWriteSerializer if self.request.method in ('PUT', 'PATCH') else ArticleSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ArticleWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        return Response(ArticleSerializer(article).data)
