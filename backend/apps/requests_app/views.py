from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PurchaseRequest
from .serializers import PurchaseRequestSerializer, PurchaseRequestCreateSerializer
from . import services
from apps.common.permissions import (
    IsAdminOrDemandeur, IsAdminOrValidateur, CanManageRequests, DEMANDEUR,
)


def _demandeur_qs(user, qs):
    """Restreint le queryset aux seules DA du demandeur connecté."""
    if user.role == DEMANDEUR:
        return qs.filter(requester=user)
    return qs


class PurchaseRequestListCreateView(generics.ListCreateAPIView):
    # GET  : tout rôle authentifié (DIRECTION inclus)
    # POST : ADMIN ou DEMANDEUR uniquement
    permission_classes = [CanManageRequests]

    def get_queryset(self):
        qs = PurchaseRequest.objects.select_related('requester').prefetch_related(
            'lines__article', 'audit'
        ).order_by('-created_at')
        return _demandeur_qs(self.request.user, qs)

    def get_serializer_class(self):
        return PurchaseRequestCreateSerializer if self.request.method == 'POST' else PurchaseRequestSerializer

    def perform_create(self, serializer):
        req = serializer.save(requester=self.request.user)
        services.add_audit_entry(req, self.request.user, 'Création')

    def create(self, request, *args, **kwargs):
        serializer = PurchaseRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response(PurchaseRequestSerializer(instance).data, status=status.HTTP_201_CREATED)


class PurchaseRequestDetailView(generics.RetrieveUpdateAPIView):
    # GET   : tout rôle authentifié
    # PATCH : ADMIN ou DEMANDEUR (et uniquement sur ses propres DAs pour DEMANDEUR)
    serializer_class = PurchaseRequestSerializer
    permission_classes = [CanManageRequests]

    def get_queryset(self):
        qs = PurchaseRequest.objects.select_related('requester').prefetch_related(
            'lines__article', 'audit'
        ).all()
        return _demandeur_qs(self.request.user, qs)


@api_view(['POST'])
@permission_classes([IsAdminOrDemandeur])
def submit_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    services.submit_purchase_request(pr, request.user)
    return Response(PurchaseRequestSerializer(pr).data)


@api_view(['POST'])
@permission_classes([IsAdminOrValidateur])
def approve_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    comment = request.data.get('comment', '')
    services.approve_purchase_request(pr, request.user, comment)
    return Response(PurchaseRequestSerializer(pr).data)


@api_view(['POST'])
@permission_classes([IsAdminOrValidateur])
def reject_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    comment = request.data.get('comment', '')
    services.reject_purchase_request(pr, request.user, comment)
    return Response(PurchaseRequestSerializer(pr).data)
