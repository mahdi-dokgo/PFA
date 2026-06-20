from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from . import services
from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer, PurchaseOrderCreateSerializer
from apps.common.permissions import (
    IsAdminOrAcheteur,
    IsAdminOrAcheteurReadAll,
    IsAdminOrAcheteurOrValidateur,
)


class POListCreateView(generics.ListCreateAPIView):
    # GET  : tout rôle authentifié (VALIDATEUR et DIRECTION inclus)
    # POST : ADMIN ou ACHETEUR uniquement
    queryset = PurchaseOrder.objects.select_related('supplier', 'request').prefetch_related(
        'lines__article'
    ).order_by('-created_at')
    permission_classes = [IsAdminOrAcheteurReadAll]

    def get_serializer_class(self):
        return PurchaseOrderCreateSerializer if self.request.method == 'POST' else PurchaseOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = serializer.save()
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)


class PODetailView(generics.RetrieveUpdateAPIView):
    # GET   : tout rôle authentifié
    # PATCH : ADMIN ou ACHETEUR uniquement
    queryset = PurchaseOrder.objects.select_related('supplier', 'request').prefetch_related(
        'lines__article'
    ).all()
    permission_classes = [IsAdminOrAcheteurReadAll]

    def get_serializer_class(self):
        return PurchaseOrderCreateSerializer if self.request.method in ('PUT', 'PATCH') else PurchaseOrderSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PurchaseOrderCreateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        po = serializer.save()
        return Response(PurchaseOrderSerializer(po).data)


@api_view(['POST'])
@permission_classes([IsAdminOrAcheteurOrValidateur])
def transition_po(request, pk):
    # ADMIN, ACHETEUR et VALIDATEUR peuvent changer le statut d'un BC
    po = get_object_or_404(PurchaseOrder, pk=pk)
    services.transition_purchase_order(po, request.data.get('status', po.status))
    return Response(PurchaseOrderSerializer(po).data)
