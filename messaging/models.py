import uuid
from django.db import models
from django.conf import settings
from collaborations.models import Application

User = settings.AUTH_USER_MODEL


class Thread(models.Model):
    """
    One conversation thread per Application.
    Created automatically when an Application is created (via signal).
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='thread')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Fil de discussion'
        verbose_name_plural = 'Fils de discussion'
        ordering            = ['-updated_at']

    def __str__(self):
        return f"Thread — {self.application}"

    @property
    def business_user(self):
        return self.application.campaign.business.user

    @property
    def influencer_user(self):
        return self.application.influencer.user

    def is_participant(self, user):
        return user == self.business_user or user == self.influencer_user


class Message(models.Model):
    """
    A single message inside a Thread.

    Types:
      user   — free text sent by a participant
      system — auto-generated event (application accepted, etc.)
      draft  — influencer submits content for brand review
    """
    class Type(models.TextChoices):
        USER   = 'user',   'Message utilisateur'
        SYSTEM = 'system', 'Événement système'
        DRAFT  = 'draft',  'Soumission de contenu'

    class DraftStatus(models.TextChoices):
        PENDING  = 'pending',  'En attente de révision'
        APPROVED = 'approved', 'Approuvé'
        CHANGES  = 'changes',  'Modifications demandées'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread       = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')

    # null for system messages (no human author)
    sender       = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_messages',
    )

    message_type = models.CharField(max_length=20, choices=Type.choices, default=Type.USER)
    body         = models.TextField(blank=True)

    # For draft messages only
    attachment   = models.FileField(upload_to='drafts/%Y/%m/', null=True, blank=True)
    draft_status = models.CharField(
        max_length=20,
        choices=DraftStatus.choices,
        null=True, blank=True,
    )

    # Read tracking — who has read this message
    read_by      = models.ManyToManyField(
        User, blank=True,
        related_name='read_messages',
    )

    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Message'
        verbose_name_plural = 'Messages'
        ordering            = ['created_at']

    def __str__(self):
        return f"[{self.get_message_type_display()}] {self.thread} — {self.created_at:%d/%m/%Y %H:%M}"