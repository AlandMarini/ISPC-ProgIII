from django.core.cache import cache
import random
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import  OTPSendSerializer, OTPValidateSerializer, PasswordResetConfirmSerializer, RegisterSerializer, UserSerializer



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

        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class OtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        code = request.data.get('code')

        if not username:
            return Response(
                {"error": "Usuario requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        cache_key = f"otp:{username}"

        if not code:
            serializer = OTPSendSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            otp = str(random.randint(1000, 9999))
            cache.set(cache_key, otp, timeout=300)

            print(f"DEBUG: OTP para {username} es {otp}")

            return Response(
                {"message": "Código enviado"},
                status=status.HTTP_200_OK
            )

        serializer = OTPValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stored_code = cache.get(cache_key)

        if not stored_code or stored_code != code:
            return Response(
                {"error": "Código inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache.delete(cache_key)

        token = AccessToken.for_user(user)
        token["type"] = "recovery"
        token["username"] = user.username

        return Response(
            {
                "message": "OTP validado correctamente",
                "recovery_token": str(token)
            },
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"error": "Token requerido"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        raw_token = auth_header.split(" ")[1]

        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(raw_token)
            user = jwt_auth.get_user(validated_token)
        except Exception:
            return Response(
                {"error": "Token inválido"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if validated_token.get("type") != "recovery":
            return Response(
                {"error": "Token no válido para recuperación"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Contraseña actualizada correctamente"},
            status=status.HTTP_200_OK
        )