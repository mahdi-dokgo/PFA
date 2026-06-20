from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Supplier
from .serializers import SupplierSerializer
from apps.common.permissions import IsAdminOrAcheteur, IsAdminOrAcheteurReadAll


class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrAcheteurReadAll]


class SupplierDetailView(generics.RetrieveUpdateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrAcheteurReadAll]


@api_view(['POST'])
@permission_classes([IsAdminOrAcheteur])
def archive_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.status = 'archived'
    supplier.save()
    return Response(SupplierSerializer(supplier).data)
