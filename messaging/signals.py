from django.db.models.signals import post_save
from django.dispatch import receiver
from collaborations.models import Application
from .models import Thread, Message


def _system_message(thread, body):
    Message.objects.create(
        thread=thread,
        sender=None,
        message_type=Message.Type.SYSTEM,
        body=body,
    )


@receiver(post_save, sender=Application)
def handle_application_lifecycle(sender, instance, created, **kwargs):

    if created:
        thread = Thread.objects.create(application=instance)

        if instance.origin == 'influencer':
            body = (
                f"📩 Candidature soumise par {instance.influencer.user.full_name}. "
                f"La discussion est maintenant ouverte."
            )
        else:
            body = (
                f"📨 Invitation envoyée à {instance.influencer.user.full_name} "
                f"par {instance.campaign.business.company_name}."
            )

        _system_message(thread, body)
        return

    # Status transitions
    STATUS_EVENTS = {
        'accepted':  "✅ Candidature acceptée. La collaboration peut commencer.",
        'rejected':  "❌ Candidature refusée.",
        'withdrawn': "↩️ Candidature retirée par l'influenceur.",
    }

    if instance.status in STATUS_EVENTS:
        thread, _ = Thread.objects.get_or_create(application=instance)
        _system_message(thread, STATUS_EVENTS[instance.status])