import uuid
from django.db import models
from profiles.models import BusinessProfile
from categories.models import Category


class Campaign(models.Model):
    """
    A campaign (brief) posted by a business.
    Starts as a draft; the business must explicitly publish it (status='open')
    so that influencers can discover and apply.
    """

    STATUS_CHOICES = (
        ('draft',       'Brouillon'),
        ('open',        'Ouverte'),
        ('paused',      'En pause'),
        ('in_progress', 'En cours'),
        ('completed',   'Terminée'),
        ('cancelled',   'Annulée'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='campaigns',
        verbose_name="Entreprise",
    )

    title              = models.CharField(max_length=200, verbose_name="Titre de la campagne")
    description        = models.TextField(verbose_name="Description globale")
    deliverables_brief = models.TextField(
        verbose_name="Brief et livrables attendus",
        help_text="Ex : 1 Reel Instagram, 2 Stories, 1 vidéo YouTube…",
    )
    budget   = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Budget global (€)")
    duration = models.CharField(max_length=100, blank=True, null=True, verbose_name="Durée", help_text="Ex: 2 semaines, 1 mois, etc.")
    deadline = models.DateField(verbose_name="Date limite de candidature")

    # Defaults to 'draft' — must be explicitly published.
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Campagne'
        verbose_name_plural = 'Campagnes'
        ordering            = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_draft(self):
        return self.status == 'draft'

    @property
    def is_open(self):
        return self.status == 'open'

    @property
    def is_paused(self):
        return self.status == 'paused'

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class CampaignCategory(models.Model):
    """
    Explicit through-table linking campaigns to categories (target niches).
    Using an explicit model gives us the ability to add extra fields later
    (e.g. priority, weight) without a migration nightmare.
    """
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='campaign_categories'
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='campaign_categories'
    )

    class Meta:
        verbose_name        = 'Catégorie de campagne'
        verbose_name_plural = 'Catégories de campagne'
        unique_together     = ('campaign', 'category')

    def __str__(self):
        return f"{self.campaign} → {self.category}"
