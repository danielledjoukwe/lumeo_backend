import uuid
from django.db import models
from django.conf import settings
from categories.models import Category

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
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name= models.CharField(max_length=255, verbose_name="Nom de l'entreprise / de la marque")
    industry    = models.CharField(max_length=100, blank=True, verbose_name="Secteur d'activité")
    website     = models.URLField(blank=True, verbose_name="Site web")
    description = models.TextField(blank=True, verbose_name="Description de l'entreprise")
    is_verified = models.BooleanField(default=False, verbose_name="Entreprise vérifiée")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Entreprise'
        verbose_name_plural = 'Profils Entreprise'

    def __str__(self):
        return self.company_name or str(self.user)
