from rest_framework import serializers
from .models import PurchaseRequest, RequestLine, AuditEntry


class AuditEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEntry
        fields = ['id', 'actor_name', 'action', 'comment', 'at']


class RequestLineSerializer(serializers.ModelSerializer):
    article_name = serializers.CharField(source='article.name', read_only=True)

    class Meta:
        model = RequestLine
        fields = ['id', 'article_id', 'article_name', 'quantity', 'justification']


class RequestLineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLine
        fields = ['article', 'quantity', 'justification']


class PurchaseRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.full_name', read_only=True)
    requester_id = serializers.IntegerField(source='requester.id', read_only=True)
    lines = RequestLineSerializer(many=True, read_only=True)
    audit = AuditEntrySerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = ['id', 'code', 'requester_id', 'requester_name', 'priority',
                  'status', 'comment', 'created_at', 'updated_at', 'lines', 'audit']


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    lines = RequestLineWriteSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = ['priority', 'status', 'lines']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        request = PurchaseRequest.objects.create(**validated_data)
        for line in lines_data:
            RequestLine.objects.create(request=request, **line)
        return request
