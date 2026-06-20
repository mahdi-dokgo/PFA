from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from . import services
from .models import Reception
from .serializers import ReceptionSerializer, ReceptionCreateSerializer
from apps.orders.models import PurchaseOrder, POLine
from apps.articles.models import Article
from apps.common.permissions import IsAdminOrMagasinierReadAll


class ReceptionListCreateView(APIView):
    # GET: any authenticated user; POST: ADMIN or MAGASINIER only
    permission_classes = [IsAdminOrMagasinierReadAll]

    def get(self, request):
        receptions = Reception.objects.select_related('po').prefetch_related(
            'lines__article'
        ).order_by('-received_at')
        return Response(ReceptionSerializer(receptions, many=True).data)

    def post(self, request):
        serializer = ReceptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        po = get_object_or_404(PurchaseOrder, pk=data['po_id'])

        lines_data = []
        for line_data in data['lines']:
            po_line = get_object_or_404(POLine, pk=line_data['po_line_id'])
            article = get_object_or_404(Article, pk=line_data['article_id'])
            lines_data.append({
                'po_line': po_line,
                'article': article,
                'ordered_quantity': line_data['ordered_quantity'],
                'received_quantity': line_data['received_quantity'],
            })

        reception = services.create_reception_with_lines(
            po=po,
            receiver=request.user,
            receiver_name=data['receiver_name'],
            notes=data.get('notes', ''),
            lines_data=lines_data,
        )

        return Response(ReceptionSerializer(reception).data, status=status.HTTP_201_CREATED)
