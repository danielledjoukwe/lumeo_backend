"""
Public campaign discovery API — influencer side.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from config.utils.role_check import check_access
from config.utils.pagination import paginate_queryset
from campaigns.models import Campaign
from campaigns.serializers import CampaignPublicListSerializer, CampaignPublicDetailSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_list(request):
    """
    Marketplace — open campaigns for influencer discovery.

    Supports:
      ?q=<str>          — search in title and description
      ?category=<uuid>  — filter by target category
      ?ordering=        — newest | oldest | budget_asc | budget_desc
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    campaigns = Campaign.objects.filter(status='open').select_related(
        'business', 'business__user'
    ).prefetch_related('campaign_categories__category')

    # Search
    q = request.query_params.get('q', '').strip()
    if q:
        from django.db.models import Q
        campaigns = campaigns.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        ).distinct()

    # Category filter
    category_id = request.query_params.get('category', '').strip()
    if category_id:
        campaigns = campaigns.filter(
            campaign_categories__category__id=category_id
        ).distinct()

    # Ordering
    ORDER_MAP = {
        'newest':      '-created_at',
        'oldest':       'created_at',
        'budget_asc':   'budget',
        'budget_desc': '-budget',
    }
    ordering  = request.query_params.get('ordering', 'newest').strip()
    campaigns = campaigns.order_by(ORDER_MAP.get(ordering, '-created_at'))

    return paginate_queryset(request, campaigns, CampaignPublicListSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_detail(request, pk):
    """Full detail of a single open campaign, including rich business info."""
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    campaign = get_object_or_404(
        Campaign.objects.select_related('business', 'business__user')
                        .prefetch_related('campaign_categories__category'),
        pk=pk,
        status='open',
    )
    serializer = CampaignPublicDetailSerializer(campaign, context={'request': request})
    return Response(serializer.data)
