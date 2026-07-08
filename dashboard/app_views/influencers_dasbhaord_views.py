"""
Influencer dashboard — single summary endpoint.

GET /api/dashboard/influencer/
Returns everything the influencer home page needs in one call:
  - stats         : missions, pending applications, pending invitations, total accepted
  - invitations   : latest 5 pending partner invitations
  - missions      : latest 5 accepted applications (active missions)
  - recent_threads: latest 5 message threads with unread count
  - marketplace   : latest 5 open campaigns not yet applied to (matching categories first)
  - suggested     : latest 5 influencers who joined the platform
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from config.utils.role_check import check_access
from profiles.models import InfluencerProfile
from campaigns.models import Campaign
from collaborations.models import Application
from messaging.models import Thread


def _get_influencer(request):
    profile, _ = InfluencerProfile.objects.get_or_create(user=request._db_user)
    return profile


def _build_application_data(app, request):
    """Compact serialization of an application for dashboard use."""
    campaign = app.campaign
    business = campaign.business
    user = business.user

    avatar_url = None
    if user.avatar:
        try:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        except Exception:
            pass

    return {
        "id":             str(app.id),
        "origin":         app.origin,
        "status":         app.status,
        "status_label":   app.get_status_display(),
        "applied_at":     app.applied_at,
        "accepted_at":    app.accepted_at,
        "proposed_rate":  str(app.proposed_rate) if app.proposed_rate else None,
        "cover_message":  app.cover_message,
        "thread_id":      str(app.thread.id) if hasattr(app, 'thread') else None,
        "campaign": {
            "id":                 str(campaign.id),
            "title":              campaign.title,
            "budget":             str(campaign.budget),
            "duration":           campaign.duration,
            "deliverables_brief": campaign.deliverables_brief,
            "status":             campaign.status,
            "categories": [
                {"id": str(cc.category.id), "name": cc.category.name}
                for cc in campaign.campaign_categories.all()
            ],
        },
        "business": {
            "company_name": business.company_name,
            "industry":     business.industry,
            "is_verified":  business.is_verified,
            "avatar":       avatar_url,
        },
    }


def _build_campaign_card(campaign, request):
    """Compact campaign card for marketplace spotlight."""
    business = campaign.business
    user = business.user

    avatar_url = None
    if user.avatar:
        try:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        except Exception:
            pass

    return {
        "id":                 str(campaign.id),
        "title":              campaign.title,
        "budget":             str(campaign.budget),
        "duration":           campaign.duration,
        "deadline":           campaign.deadline,
        "deliverables_brief": campaign.deliverables_brief,
        "categories": [
            {"id": str(cc.category.id), "name": cc.category.name}
            for cc in campaign.campaign_categories.all()
        ],
        "business": {
            "company_name": business.company_name,
            "industry":     business.industry,
            "is_verified":  business.is_verified,
            "avatar":       avatar_url,
        },
    }


def _build_thread_data(thread, user, request):
    """Compact thread preview for the messages widget."""
    other = thread.influencer_user if user == thread.business_user else thread.business_user

    avatar_url = None
    if other.avatar:
        try:
            avatar_url = request.build_absolute_uri(other.avatar.url)
        except Exception:
            pass

    last_msg = thread.messages.order_by('-created_at').first()
    unread   = thread.messages.exclude(read_by=user).exclude(sender=user).count()

    return {
        "id":               str(thread.id),
        "campaign_title":   thread.application.campaign.title,
        "other_party_name": other.full_name,
        "other_party_avatar": avatar_url,
        "last_message": {
            "body":       last_msg.body[:80] if last_msg else "",
            "created_at": last_msg.created_at if last_msg else None,
        },
        "unread_count": unread,
        "updated_at":   thread.updated_at,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def influencer_dashboard(request):
    """
    Single endpoint that returns all data needed for the influencer home page.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    user       = request._db_user

    # ── 1. Stats ──────────────────────────────────────────────────────────────
    base_qs = Application.objects.filter(influencer=influencer)

    missions_count     = base_qs.filter(status='accepted').count()
    pending_apps_count = base_qs.filter(status='pending', origin='influencer').count()
    invitations_count  = base_qs.filter(status='pending', origin='partner').count()
    total_accepted     = missions_count  # same — accepted = all-time missions

    stats = {
        "missions_en_cours":        missions_count,
        "candidatures_en_attente":  pending_apps_count,
        "invitations_en_attente":   invitations_count,
        "missions_total_acceptees": total_accepted,
    }

    # ── 2. Pending invitations (from partners) ────────────────────────────────
    invitations_qs = (
        base_qs
        .filter(status='pending', origin='partner')
        .select_related(
            'campaign', 'campaign__business', 'campaign__business__user',
        )
        .prefetch_related('campaign__campaign_categories__category')
        .order_by('-applied_at')[:5]
    )
    invitations = [_build_application_data(a, request) for a in invitations_qs]

    # ── 3. Active missions (accepted applications) ────────────────────────────
    missions_qs = (
        base_qs
        .filter(status='accepted')
        .select_related(
            'campaign', 'campaign__business', 'campaign__business__user',
        )
        .prefetch_related('campaign__campaign_categories__category')
        .order_by('-accepted_at')[:5]
    )
    missions = [_build_application_data(a, request) for a in missions_qs]

    # ── 4. Recent threads ─────────────────────────────────────────────────────
    threads_qs = (
        Thread.objects
        .filter(application__influencer=influencer)
        .select_related(
            'application',
            'application__campaign',
            'application__campaign__business',
            'application__campaign__business__user',
            'application__influencer__user',
        )
        .prefetch_related('messages')
        .order_by('-updated_at')[:5]
    )
    recent_threads = [_build_thread_data(t, user, request) for t in threads_qs]

    # ── 5. Marketplace spotlight ──────────────────────────────────────────────
    # Campaigns already applied to (no duplicates)
    already_applied_ids = base_qs.values_list('campaign_id', flat=True)

    # Influencer's own category ids for relevance boost
    my_category_ids = influencer.categories.values_list('id', flat=True)

    open_campaigns = (
        Campaign.objects
        .filter(status='open')
        .exclude(id__in=already_applied_ids)
        .select_related('business', 'business__user')
        .prefetch_related('campaign_categories__category')
    )

    # Matching categories first, then the rest — take top 5
    matching    = open_campaigns.filter(campaign_categories__category__id__in=my_category_ids).distinct()
    non_matching = open_campaigns.exclude(campaign_categories__category__id__in=my_category_ids).distinct()

    spotlight_ids   = set()
    spotlight_cards = []
    for c in list(matching[:5]) + list(non_matching[:5]):
        if c.id not in spotlight_ids and len(spotlight_cards) < 5:
            spotlight_ids.add(c.id)
            spotlight_cards.append(_build_campaign_card(c, request))

    # ── 6. Recently joined influencers (suggested section) ───────────────────
    recent_influencers_qs = (
        InfluencerProfile.objects
        .exclude(user=user)
        .select_related('user')
        .prefetch_related('platforms', 'categories')
        .order_by('-created_at')[:5]
    )

    suggested_influencers = []
    for inf in recent_influencers_qs:
        inf_user   = inf.user
        avatar_url = None
        if inf_user.avatar:
            try:
                avatar_url = request.build_absolute_uri(inf_user.avatar.url)
            except Exception:
                pass

        # Total followers across all platforms
        total_followers = sum(p.followers for p in inf.platforms.all())

        suggested_influencers.append({
            "id":             str(inf.id),
            "full_name":      inf_user.full_name,
            "city":           inf_user.city,
            "country":        inf_user.country,
            "avatar":         avatar_url,
            "bio":            inf.bio,
            "is_verified":    inf.is_verified,
            "total_followers": total_followers,
            "platforms": [
                {
                    "platform":    p.platform,
                    "profile_url": p.profile_url,
                    "followers":   p.followers,
                }
                for p in inf.platforms.all()
            ],
            "categories": [
                {"id": str(c.id), "name": c.name}
                for c in inf.categories.all()
            ],
        })

    return Response({
        "stats":                stats,
        "invitations":          invitations,
        "missions":             missions,
        "recent_threads":       recent_threads,
        "marketplace_spotlight": spotlight_cards,
        "suggested_influencers": suggested_influencers,
    })
