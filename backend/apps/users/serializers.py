from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, default='changeme123')

    class Meta:
        model = User
        fields = ['email', 'full_name', 'role', 'is_active', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', 'changeme123')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
