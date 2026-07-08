from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from config.utils.pagination import paginate_queryset
from messaging.models import Thread
from messaging.serializers import ThreadSerializer, MessageSerializer


def _assert_participant(thread, user):
    """Returns 403 response if user is not a thread participant, else None."""
    if not thread.is_participant(user):
        return Response(
            {"error": "Vous n'êtes pas autorisé à accéder à cette discussion."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_thread_list(request):
    """
    List all threads the authenticated user participates in.
    Works for both influencer and business users.
    """
    user = request.user

    threads = Thread.objects.filter(
        Q(application__influencer__user=user) |
        Q(application__campaign__business__user=user)
    ).select_related(
        'application',
        'application__campaign',
        'application__campaign__business',
        'application__campaign__business__user',
        'application__influencer',
        'application__influencer__user',
    ).prefetch_related('messages').order_by('-updated_at')

    return paginate_queryset(request, threads, ThreadSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def thread_detail(request, pk):
    """
    Retrieve a thread with its full message history.
    Marks all messages as read for the current user.
    """
    thread = get_object_or_404(Thread, pk=pk)

    error = _assert_participant(thread, request.user)
    if error:
        return error

    # Mark all unread messages as read
    unread = thread.messages.exclude(read_by=request.user).exclude(sender=request.user)
    for msg in unread:
        msg.read_by.add(request.user)

    messages_qs = thread.messages.all()
    return Response({
        'thread':   ThreadSerializer(thread, context={'request': request}).data,
        'messages': MessageSerializer(messages_qs, many=True, context={'request': request}).data,
    })