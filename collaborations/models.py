import uuid
from django.db import models
from django.conf import settings
from campaigns.models import Campaign
from profiles.models import InfluencerProfile

User = settings.AUTH_USER_MODEL


class Application(models.Model):
    """
    An influencer's application (candidature) to a campaign.

    Lifecycle:
        pending   → accepted  — Enterprise accepts. The application becomes a mission.
                                The influencer executes the work outside the platform.
        pending   → rejected  — Enterprise declined.
        pending   → withdrawn — Influencer cancelled before a decision.

    One influencer can only apply once per campaign (unique_together).
    Multiple applications on the same campaign can be accepted — there is no
    artificial cap; the enterprise decides when to stop reviewing.

    Note: in_progress / completed statuses are reserved for a future
    deliverable-submission workflow and are not used at this stage.
    """

    STATUS_CHOICES = (
        ('pending',   'En attente'),
        ('accepted',  'Acceptée'),
        ('rejected',  'Refusée'),
        ('withdrawn', "Retirée par l'influenceur"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Origin ────────────────────────────────────────────────────────────────
    ORIGIN_CHOICES = (
        ('influencer', 'Candidature de l\'influenceur'),
        ('partner',    'Invitation du partenaire'),
    )
    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default='influencer',
        verbose_name="Origine",
    )

    # ── Participants ──────────────────────────────────────────────────────────
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Campagne",
    )
    influencer = models.ForeignKey(
        InfluencerProfile,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Influenceur",
    )

    # ── Application content ───────────────────────────────────────────────────
    cover_message = models.TextField(
        verbose_name="Message de candidature",
        help_text=(
            "L'influenceur présente sa motivation, son audience, "
            "et explique pourquoi il est le bon profil pour cette campagne."
        ),
    )
    proposed_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tarif proposé (FCFA)",
        help_text=(
            "Optionnel. Si l'influenceur souhaite proposer un tarif différent "
            "du budget indiqué dans la campagne."
        ),
    )

    # ── Status & review ───────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut",
    )
    enterprise_note = models.TextField(
        blank=True,
        verbose_name="Note de l'entreprise",
        help_text="Visible par l'influenceur. Motif de refus ou message d'accompagnement.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    applied_at  = models.DateTimeField(auto_now_add=True, verbose_name="Date de candidature")
    accepted_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date d'acceptation",
        help_text="Set automatically when the enterprise accepts the application.",
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de révision",
        help_text="Set on any final decision: accepted, rejected, or withdrawn.",
    )
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Candidature'
        verbose_name_plural = 'Candidatures'
        ordering            = ['-applied_at']
        unique_together     = ('campaign', 'influencer')

    def __str__(self):
        return f"{self.influencer} → {self.campaign} [{self.get_status_display()}]"

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_accepted(self):
        return self.status == 'accepted'

    @property
    def can_be_withdrawn(self):
        """Influencer can only withdraw while still pending."""
        return self.status == 'pending'

    @property
    def can_be_reviewed(self):
        """Enterprise can only accept/reject pending applications."""
        return self.status == 'pending'

    @property
    def is_invitation(self):
        """True when the partner initiated the collaboration."""
        return self.origin == 'partner'
