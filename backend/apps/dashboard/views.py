from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, F
from apps.requests_app.models import PurchaseRequest
from apps.orders.models import PurchaseOrder
from apps.articles.models import Article


class KpisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'total_requests': PurchaseRequest.objects.count(),
            'pending_validations': PurchaseRequest.objects.filter(status='SOUMISE').count(),
            'active_orders': PurchaseOrder.objects.filter(
                status__in=['APPROUVEE', 'ENVOYEE', 'PARTIELLEMENT_RECUE']
            ).count(),
            'critical_stock': Article.objects.filter(current_stock__lt=F('min_threshold')).count(),
        })


class RequestsPerPeriodView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models.functions import TruncWeek
        data = (
            PurchaseRequest.objects
            .annotate(period=TruncWeek('created_at'))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')[:8]
        )
        return Response([
            {'period': f"Sem. {d['period'].isocalendar()[1]}", 'count': d['count']}
            for d in data
        ])


class OrdersByStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = PurchaseOrder.objects.values('status').annotate(count=Count('id'))
        return Response([{'status': d['status'], 'count': d['count']} for d in data])


class SpendBySupplierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            PurchaseOrder.objects
            .values('supplier__name')
            .annotate(total=Sum('total_amount'))
            .order_by('-total')[:10]
        )
        return Response([{'name': d['supplier__name'], 'total': float(d['total'] or 0)} for d in data])


class MostRequestedArticlesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.requests_app.models import RequestLine
        data = (
            RequestLine.objects
            .values('article__name')
            .annotate(total=Sum('quantity'))
            .order_by('-total')[:5]
        )
        return Response([{'name': d['article__name'], 'total': d['total']} for d in data])


class LateOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.orders.serializers import PurchaseOrderSerializer
        today = timezone.now().date()
        orders = PurchaseOrder.objects.filter(
            expected_date__lt=today
        ).exclude(
            status__in=['RECUE', 'CLOTUREE', 'ANNULEE']
        ).select_related('supplier').prefetch_related('lines__article')
        return Response(PurchaseOrderSerializer(orders, many=True).data)
