"""
Influencer-side mission API.

All endpoints require the authenticated user to have the 'influencer' role.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from config.utils.role_check import check_access
from config.utils.pagination import paginate_queryset
from profiles.models import InfluencerProfile
from collaborations.models import Application
from collaborations.serializers import ApplicationInfluencerSerializer

# A mission is simply an accepted application
MISSION_STATUSES = ('accepted',)


def _get_influencer(request):
    """Return the InfluencerProfile for the authenticated user."""
    profile, _ = InfluencerProfile.objects.get_or_create(user=request._db_user)
    return profile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_mission_list(request):
    """
    List all missions for the authenticated influencer.
    A mission is an application that has been accepted.

    Supports:
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    missions   = Application.objects.filter(
        influencer=influencer,
        status__in=MISSION_STATUSES,
    ).select_related(
        'campaign',
        'campaign__business',
        'campaign__business__user',
    ).prefetch_related('campaign__campaign_categories__category')

    status_filter = request.query_params.get('status', '').strip()
    if status_filter and status_filter in MISSION_STATUSES:
        missions = missions.filter(status=status_filter)

    missions = missions.order_by('-accepted_at')

    return paginate_queryset(request, missions, ApplicationInfluencerSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_mission_detail(request, pk):
    """
    Retrieve the detail of a single mission.
    The application must belong to the influencer and be in a mission status.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    mission    = get_object_or_404(
        Application,
        pk=pk,
        influencer=influencer,
        status__in=MISSION_STATUSES,
    )
    return Response(
        ApplicationInfluencerSerializer(mission, context={'request': request}).data
    )
