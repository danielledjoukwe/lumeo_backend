# ── API Views ─────────────────────────────────────────────────────────────────

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.conf import settings
from config.utils.email import send_email
import random
import string
from ..models import User
from ..serializers import (
    RegisterSerializer, VerifyEmailSerializer, ResendVerificationSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, UserSerializer
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(user, code):
    send_email(
        template='auth/email/verification_code.html',
        context={
            'user_name': user.first_name or user.email,
            'code': code,
        },
        subject=f'[{settings.APP_NAME}] Code de vérification : {code}',
        recipient=user.email,
    )

def send_password_reset_email(user, token):
    # Point the link to the React frontend route
    reset_url = f"{settings.FRONTEND_URL}/reset-password?email={user.email}&token={token}"
    send_email(
        template='auth/email/password_reset.html',
        context={
            'user_name': user.first_name or user.email,
            'reset_url': reset_url,
        },
        subject=f'[{settings.APP_NAME}] Réinitialisation de votre mot de passe',
        recipient=user.email,
    )

# ── API Endpoints ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        code = generate_verification_code()
        # Store code in cache for 10 minutes (600 seconds)
        cache.set(f"email_verification_{user.email}", code, 600)
        send_verification_email(user, code)
        return Response({"message": "Compte créé. Veuillez vérifier votre e-mail."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_api_view(request):
    serializer = VerifyEmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        stored_code = cache.get(f"email_verification_{email}")
        
        if not stored_code:
            return Response({"error": "Code expiré ou introuvable."}, status=status.HTTP_400_BAD_REQUEST)
            
        if code == stored_code:
            try:
                user = User.objects.get(email=email)
                user.is_email_verified = True
                user.save()
                cache.delete(f"email_verification_{email}")
                return Response({"message": "Compte vérifié avec succès."})
            except User.DoesNotExist:
                return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Code incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_api_view(request):
    serializer = ResendVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return Response({"error": "Ce compte est déjà vérifié."}, status=status.HTTP_400_BAD_REQUEST)
                
            code = generate_verification_code()
            cache.set(f"email_verification_{email}", code, 600)
            send_verification_email(user, code)
            return Response({"message": "Un nouveau code a été envoyé."})
        except User.DoesNotExist:
            return Response({"error": "Aucun compte trouvé avec cet e-mail."}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api_view(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    
    # Ensure `authenticate` is imported in your file (from django.contrib.auth import authenticate)
    user = authenticate(request, username=email, password=password)
    if user is not None:
        # Staff/admin users bypass the email verification requirement
        if not user.is_staff and not user.is_email_verified:
            return Response({"error": "Veuillez vérifier votre e-mail avant de vous connecter."}, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    return Response({"error": "E-mail ou mot de passe incorrect."}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_api_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = generate_verification_code()
            cache.set(f"password_reset_{email}", token, 1800) # 30 mins
            send_password_reset_email(user, token)
        except User.DoesNotExist:
            pass # Don't reveal if user exists
        return Response({"message": "Si cet e-mail existe, un lien de réinitialisation a été envoyé."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_api_view(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        stored_token = cache.get(f"password_reset_{email}")
        if not stored_token or stored_token != token:
            return Response({"error": "Lien invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            cache.delete(f"password_reset_{email}")
            return Response({"message": "Mot de passe réinitialisé avec succès."})
        except User.DoesNotExist:
            return Response({"error": "Compte introuvable."}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api_view(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Jeton de rafraîchissement manquant."}, status=status.HTTP_400_BAD_REQUEST)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": "Jeton invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)
