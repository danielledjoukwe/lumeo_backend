import random
import string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError
from config.utils.email import send_email
from .models import User


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
    reset_url = f"{settings.SITE_URL}/auth/reset-password/?token={token}"
    send_email(
        template='auth/email/password_reset.html',
        context={
            'user_name': user.first_name or user.email,
            'reset_url': reset_url,
        },
        subject=f'[{settings.APP_NAME}] Réinitialisation de votre mot de passe',
        recipient=user.email,
    )


# ── Register ─────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_business:
            return redirect('enterprise_home')
        return redirect('influencer_home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')
        role       = request.POST.get('role', '')

        # Validation
        if not all([first_name, last_name, email, password1, password2, role]):
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'auth/register.html')

        if role not in [User.Role.BUSINESS, User.Role.INFLUENCER]:
            messages.error(request, 'Veuillez sélectionner un rôle valide.')
            return render(request, 'auth/register.html')

        if password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'auth/register.html')

        if len(password1) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            return render(request, 'auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Un compte avec cette adresse e-mail existe déjà. Connectez-vous ou utilisez une autre adresse.')
            return render(request, 'auth/register.html')

        # Create user — wrapped in IntegrityError catch as a race-condition safety net
        try:
            user = User.objects.create_user(
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True,
                is_email_verified=False,
            )
        except IntegrityError:
            messages.error(request, 'Un compte avec cette adresse e-mail existe déjà. Connectez-vous ou utilisez une autre adresse.')
            return render(request, 'auth/register.html')

        # Generate and store verification code in session
        code = generate_verification_code()
        request.session['verification_code'] = code
        request.session['verification_email'] = email
        request.session['verification_code_created'] = timezone.now().isoformat()

        send_verification_email(user, code)

        return redirect('verify_email')

    return render(request, 'auth/register.html')


# ── Verify email ─────────────────────────────────────────────────────────────

def verify_email_view(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('resend_verification')

    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        stored_code  = request.session.get('verification_code')
        created_at   = request.session.get('verification_code_created')

        # Check expiry (10 minutes)
        if created_at:
            from datetime import datetime, timezone as dt_timezone
            created = datetime.fromisoformat(created_at)
            elapsed = (datetime.now(dt_timezone.utc) - created).total_seconds()
            if elapsed > 600:
                messages.error(request, 'Le code a expiré. Veuillez en demander un nouveau.')
                return render(request, 'auth/verify_email.html', {'email': email})

        if entered_code == stored_code:
            try:
                user = User.objects.get(email=email)
                user.is_email_verified = True
                user.save()
                # Clear session
                del request.session['verification_code']
                del request.session['verification_email']
                del request.session['verification_code_created']
                messages.success(request, 'Compte vérifié avec succès. Vous pouvez maintenant vous connecter.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Compte introuvable.')
        else:
            messages.error(request, 'Code incorrect. Veuillez réessayer.')

    return render(request, 'auth/verify_email.html', {'email': email})


# ── Resend verification ───────────────────────────────────────────────────────

def resend_verification_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                messages.error(request, 'Ce compte est déjà vérifié.')
                return redirect('login')

            code = generate_verification_code()
            request.session['verification_code'] = code
            request.session['verification_email'] = email
            request.session['verification_code_created'] = timezone.now().isoformat()

            send_verification_email(user, code)
            return redirect('verify_email')

        except User.DoesNotExist:
            messages.error(request, 'Aucun compte trouvé avec cet e-mail.')

    return render(request, 'auth/resend_verification.html')


# ── Login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_home')
        if request.user.is_business:
            return redirect('enterprise_home')
        return redirect('influencer_home')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if not user.is_email_verified:
                request.session['verification_email'] = email
                messages.error(request, 'Veuillez vérifier votre e-mail avant de vous connecter.')
                return redirect('verify_email')
            login(request, user)
            # Redirect based on role — staff/superusers go to the admin panel
            if user.is_staff:
                return redirect('admin_home')
            elif user.is_business:
                return redirect('enterprise_home')
            elif user.is_influencer:
                return redirect('influencer_home')
            return redirect('home')
        else:
            messages.error(request, 'E-mail ou mot de passe incorrect.')

    return render(request, 'auth/login.html')


# ── Logout ────────────────────────────────────────────────────────────────────

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


# ── Forgot password ───────────────────────────────────────────────────────────

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            token = generate_verification_code()
            request.session['reset_token'] = token
            request.session['reset_email'] = email
            request.session['reset_token_created'] = timezone.now().isoformat()
            send_password_reset_email(user, token)
            messages.success(request, 'Un lien de réinitialisation a été envoyé à votre e-mail.')
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            messages.success(request, 'Si cet e-mail existe, un lien de réinitialisation a été envoyé.')

    return render(request, 'auth/forgot_password.html')


# ── Reset password ────────────────────────────────────────────────────────────

def reset_password_view(request):
    token = request.GET.get('token') or request.POST.get('token')
    stored_token = request.session.get('reset_token')
    email = request.session.get('reset_email')

    if not token or token != stored_token or not email:
        messages.error(request, 'Lien invalide ou expiré.')
        return redirect('forgot_password')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'auth/reset_password.html', {'token': token})

        if len(password1) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            return render(request, 'auth/reset_password.html', {'token': token})

        # Check token expiry (30 minutes)
        created_at = request.session.get('reset_token_created')
        if created_at:
            from datetime import datetime, timezone as dt_timezone
            created = datetime.fromisoformat(created_at)
            elapsed = (datetime.now(dt_timezone.utc) - created).total_seconds()
            if elapsed > 1800:
                messages.error(request, 'Le lien a expiré. Veuillez en demander un nouveau.')
                return redirect('forgot_password')

        try:
            user = User.objects.get(email=email)
            user.set_password(password1)
            user.save()
            del request.session['reset_token']
            del request.session['reset_email']
            del request.session['reset_token_created']
            messages.success(request, 'Mot de passe réinitialisé avec succès.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Compte introuvable.')
            return redirect('forgot_password')

    return render(request, 'auth/reset_password.html', {'token': token})
