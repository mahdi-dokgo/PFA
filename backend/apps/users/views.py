from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer, CreateUserSerializer
from apps.common.permissions import IsAdmin


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('full_name')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        return CreateUserSerializer if self.request.method == 'POST' else UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


@api_view(['POST'])
@permission_classes([IsAdmin])
def deactivate_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = request.data.get('is_active', False)
    user.save()
    return Response(UserSerializer(user).data)


@api_view(['PUT'])
@permission_classes([IsAdmin])
def set_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.role = request.data.get('role', user.role)
    user.save()
    return Response(UserSerializer(user).data)
