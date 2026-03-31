from django.core.cache import cache
import random

from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import OTPValidateSerializer, RegisterSerializer, UserSerializer

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class OtpView(APIView):
    permission_classes = (AllowAny,)
    serializer_validate = OTPValidateSerializer

    def post(self, request):
        username = request.data.get('username')
        code = request.data.get('code')
        
        if not username:
            return Response({"error": "Usuario requerido"}, status=404)
        
        if not code:
            otp = str(random.randint(1000, 9999))
            cache.set(username, otp, timeout=300)
            print(f"DEBUG: OTP para {username} es {otp}")
            return Response({"message": "Código enviado"})
        
        serializer = OTPValidateSerializer(data=request.data)
        if serializer.is_valid():
            if cache.get(username) == code:
                cache.delete(username)
                return Response({"token": "JWT"})
            
        return Response({"error": "Código inválido o expirado"}, status=400)
