import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    """
    In-app alerts and notifications for users.
    """
    NOTIFICATION_TYPES = (
        ('application_received', 'Candidature reçue'),
        ('application_update', 'Mise à jour de candidature'),
        ('new_message', 'Nouveau message'),
        ('deliverable_status', 'Statut du livrable'),
        ('system_alert', 'Alerte système'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=150)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True, help_text="URL interne pour l'action")
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif: {self.title} pour {self.recipient}"
