import uuid
from django.db import models
from django.conf import settings
from categories.models import Category
from config.utils.file_validators import validate_document_extension

User = settings.AUTH_USER_MODEL


class InfluencerProfile(models.Model):
    """
    Extended profile for an influencer/creator.
    Personal info (name, avatar, bio) lives on the User model.
    This model holds influencer-specific data.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='influencer_profile')
    categories  = models.ManyToManyField(Category, related_name='influencers', blank=True, verbose_name="Niches / Domaines")
    bio         = models.TextField(blank=True, verbose_name="Bio")
    is_verified = models.BooleanField(default=False, verbose_name="Profil vérifié")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Influenceur'
        verbose_name_plural = 'Profils Influenceur'

    def __str__(self):
        return str(self.user)


class SocialPlatform(models.Model):
    """
    A social media account linked to an influencer's profile.
    Each row represents one platform the influencer is active on.
    """
    PLATFORM_CHOICES = (
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter / X'),
        ('facebook', 'Facebook'),
        ('snapchat', 'Snapchat'),
        ('linkedin', 'LinkedIn'),
        ('other', 'Autre'),
    )

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile     = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='platforms')
    platform    = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name="Plateforme")
    profile_url = models.URLField(verbose_name="Lien du profil")
    followers   = models.PositiveIntegerField(default=0, verbose_name="Nombre d'abonnés")

    class Meta:
        verbose_name = 'Plateforme sociale'
        verbose_name_plural = 'Plateformes sociales'
        unique_together = ('profile', 'platform')
        ordering = ['platform']

    def __str__(self):
        return f"{self.get_platform_display()} — {self.profile}"


class BusinessProfile(models.Model):
    """
    Profile for a business (brand/artist).
    Personal info lives on the User model.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('individual',    'Particulier / Artiste'),
        ('organization',  'Organisation / Entreprise'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('none',      'Non soumis'),
        ('pending',   'En attente de révision'),
        ('approved',  'Approuvé'),
        ('rejected',  'Rejeté'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name= models.CharField(max_length=255, verbose_name="Nom de l'entreprise / de la marque")
    industry    = models.CharField(max_length=100, blank=True, verbose_name="Secteur d'activité")
    website     = models.URLField(blank=True, verbose_name="Site web")
    description = models.TextField(blank=True, verbose_name="Description de l'entreprise")
    
    # Verification fields
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='individual',
        verbose_name="Type de compte",
    )
    niu = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="NIU (Numéro d'Identifiant Unique)",
        help_text="Optionnel. Le NIU renforce la crédibilité du dossier.",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='none',
        verbose_name="Statut de vérification",
    )
    verification_note = models.TextField(
        blank=True,
        verbose_name="Note de l'administrateur",
        help_text="Visible par le partenaire. Expliquer le motif de rejet ou les corrections à apporter.",
    )
    verification_requested_at = models.DateTimeField(null=True, blank=True)
    verification_reviewed_at  = models.DateTimeField(null=True, blank=True)

    is_verified = models.BooleanField(default=False, verbose_name="Entreprise vérifiée")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Entreprise'
        verbose_name_plural = 'Profils Entreprise'

    def __str__(self):
        return self.company_name or str(self.user)

    def save(self, *args, **kwargs):
        # Auto-sync is_verified with approved status
        self.is_verified = (self.verification_status == 'approved')
        super().save(*args, **kwargs)


class VerificationDocument(models.Model):
    """
    Document officiel soumis par un partenaire dans le cadre
    de sa demande de vérification.
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile     = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='verification_documents',
    )
    document_name = models.CharField(
        max_length=150,
        verbose_name="Nom du document",
        help_text="Ex : CNI, Récépissé, RCCM, Passeport, Attestation fiscale…",
    )
    file = models.FileField(
        upload_to='verification_documents/%Y/%m/',
        validators=[validate_document_extension],
        verbose_name="Fichier",
        help_text="PDF, JPG ou PNG. Max 5 Mo.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Document de vérification'
        verbose_name_plural = 'Documents de vérification'
        ordering            = ['uploaded_at']

    def __str__(self):
        return f"{self.document_name} — {self.profile}"
