import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = settings.AUTH_USER_MODEL

class ActionHistory(models.Model):
    """
    Audit log storing every significant action or change performed by users in the system.
    """
    ACTION_TYPES = (
        ('create', 'Création'),
        ('update', 'Mise à jour'),
        ('delete', 'Suppression'),
        ('status_change', 'Changement de statut'),
        ('login', 'Connexion'),
        ('verification', 'Vérification'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_history')
    
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    
    # Generic relation to link this action to any model (e.g., Campaign, Collaboration, Profile)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50) # Use CharField for UUIDs
    content_object = GenericForeignKey('content_type', 'object_id')
    
    description = models.TextField(help_text="Description lisible de l'action effectuée")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique d\'action'
        verbose_name_plural = 'Historiques d\'actions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.created_at}"
