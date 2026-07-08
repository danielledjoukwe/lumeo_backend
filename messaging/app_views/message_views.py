from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from messaging.models import Thread, Message
from messaging.serializers import MessageSerializer


def _assert_participant(thread, user):
    if not thread.is_participant(user):
        return Response(
            {"error": "Vous n'êtes pas autorisé à accéder à cette discussion."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def send_message(request, thread_pk):
    """
    Send a user message or draft submission to a thread.

    For a regular message:
      body — text content

    For a draft submission (influencer only, application must be accepted):
      body        — optional note
      attachment  — the content file
      message_type = 'draft'
    """
    thread = get_object_or_404(Thread, pk=thread_pk)

    error = _assert_participant(thread, request.user)
    if error:
        return error

    message_type = request.data.get('message_type', Message.Type.USER)
    body         = request.data.get('body', '').strip()
    attachment   = request.FILES.get('attachment')

    # Validate
    if message_type == Message.Type.USER and not body:
        return Response({"error": "Le message ne peut pas être vide."}, status=status.HTTP_400_BAD_REQUEST)

    if message_type == Message.Type.DRAFT:
        # Only influencer can submit drafts
        if request.user != thread.influencer_user:
            return Response(
                {"error": "Seul l'influenceur peut soumettre du contenu."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Application must be accepted before submitting drafts
        if thread.application.status != 'accepted':
            return Response(
                {"error": "La candidature doit être acceptée avant de soumettre du contenu."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not attachment:
            return Response({"error": "Un fichier est requis pour une soumission de contenu."}, status=status.HTTP_400_BAD_REQUEST)

    message = Message.objects.create(
        thread       = thread,
        sender       = request.user,
        message_type = message_type,
        body         = body,
        attachment   = attachment,
        draft_status = Message.DraftStatus.PENDING if message_type == Message.Type.DRAFT else None,
    )

    # Update thread timestamp so it bubbles up in the inbox
    thread.save(update_fields=['updated_at'])

    return Response(
        MessageSerializer(message, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def review_draft(request, thread_pk, message_pk):
    """
    Business reviews a draft: approve or request changes.

    Body:
      draft_status — 'approved' or 'changes'
      body         — optional feedback note
    """
    thread  = get_object_or_404(Thread, pk=thread_pk)
    message = get_object_or_404(Message, pk=message_pk, thread=thread, message_type=Message.Type.DRAFT)

    error = _assert_participant(thread, request.user)
    if error:
        return error

    # Only the business side can review drafts
    if request.user != thread.business_user:
        return Response(
            {"error": "Seule l'entreprise peut valider le contenu."},
            status=status.HTTP_403_FORBIDDEN,
        )

    new_status = request.data.get('draft_status')
    if new_status not in (Message.DraftStatus.APPROVED, Message.DraftStatus.CHANGES):
        return Response(
            {"error": "draft_status doit être 'approved' ou 'changes'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    message.draft_status = new_status
    message.save(update_fields=['draft_status'])

    # Auto-post a system message summarising the decision
    label = "approuvé ✅" if new_status == Message.DraftStatus.APPROVED else "des modifications demandées 🔄"
    feedback = request.data.get('body', '').strip()

    Message.objects.create(
        thread       = thread,
        sender       = None,
        message_type = Message.Type.SYSTEM,
        body         = f"Contenu {label}.{(' Feedback : ' + feedback) if feedback else ''}",
    )

    return Response(MessageSerializer(message, context={'request': request}).data)