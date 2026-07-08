"""
Partner (enterprise) dashboard — single summary endpoint.

GET /api/dashboard/partner/
Returns everything the partner home page needs in one call:
  - stats              : active campaigns, pending applications, drafts, unread messages
  - pending_approvals  : latest 5 draft messages awaiting content review
  - active_campaigns   : latest 5 active/open campaigns with accepted influencer count
  - recent_threads     : latest 5 threads with unread count
  - suggested_influencers: latest 5 influencers who joined the platform
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q

from config.utils.role_check import check_access
from profiles.models import BusinessProfile, InfluencerProfile
from campaigns.models import Campaign
from collaborations.models import Application
from messaging.models import Thread, Message


def _get_business(request):
    profile, _ = BusinessProfile.objects.get_or_create(user=request._db_user)
    return profile


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
def partner_dashboard(request):
    """
    Single endpoint that returns all data needed for the partner home page.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    user     = request._db_user

    # All campaigns belonging to this business
    my_campaigns = Campaign.objects.filter(business=business)

    # ── 1. Stats ──────────────────────────────────────────────────────────────
    active_campaigns_count  = my_campaigns.filter(status__in=('open', 'in_progress')).count()
    draft_campaigns_count   = my_campaigns.filter(status='draft').count()

    # Pending applications across all their campaigns
    pending_applications_count = Application.objects.filter(
        campaign__business=business,
        status='pending',
    ).count()

    # Unread messages across all threads linked to their campaigns
    unread_messages_count = (
        Message.objects
        .filter(thread__application__campaign__business=business)
        .exclude(read_by=user)
        .exclude(sender=user)
        .count()
    )

    stats = {
        "campagnes_actives":       active_campaigns_count,
        "campagnes_brouillon":     draft_campaigns_count,
        "candidatures_en_attente": pending_applications_count,
        "messages_non_lus":        unread_messages_count,
    }

    # ── 2. Content pending approval (draft messages awaiting review) ──────────
    pending_drafts_qs = (
        Message.objects
        .filter(
            thread__application__campaign__business=business,
            message_type=Message.Type.DRAFT,
            draft_status=Message.DraftStatus.PENDING,
        )
        .select_related(
            'thread',
            'thread__application',
            'thread__application__campaign',
            'thread__application__influencer',
            'thread__application__influencer__user',
            'sender',
        )
        .order_by('-created_at')[:5]
    )

    pending_approvals = []
    for msg in pending_drafts_qs:
        inf      = msg.thread.application.influencer
        inf_user = inf.user

        avatar_url = None
        if inf_user.avatar:
            try:
                avatar_url = request.build_absolute_uri(inf_user.avatar.url)
            except Exception:
                pass

        pending_approvals.append({
            "message_id":    str(msg.id),
            "thread_id":     str(msg.thread.id),
            "campaign_title": msg.thread.application.campaign.title,
            "submitted_at":  msg.created_at,
            "attachment":    request.build_absolute_uri(msg.attachment.url) if msg.attachment else None,
            "note":          msg.body,
            "influencer": {
                "id":         str(inf.id),
                "full_name":  inf_user.full_name,
                "avatar":     avatar_url,
                "is_verified": inf.is_verified,
            },
        })

    # ── 3. Active campaigns table ─────────────────────────────────────────────
    active_campaigns_qs = (
        my_campaigns
        .filter(status__in=('open', 'in_progress'))
        .prefetch_related('campaign_categories__category')
        .annotate(accepted_count=Count(
            'applications', filter=Q(applications__status='accepted')
        ))
        .order_by('-created_at')[:5]
    )

    active_campaigns = []
    for c in active_campaigns_qs:
        active_campaigns.append({
            "id":               str(c.id),
            "title":            c.title,
            "budget":           str(c.budget),
            "duration":         c.duration,
            "deadline":         c.deadline,
            "status":           c.status,
            "status_label":     c.status_label,
            "accepted_count":   c.accepted_count,
            "categories": [
                {"id": str(cc.category.id), "name": cc.category.name}
                for cc in c.campaign_categories.all()
            ],
        })

    # ── 4. Recent threads ─────────────────────────────────────────────────────
    threads_qs = (
        Thread.objects
        .filter(application__campaign__business=business)
        .select_related(
            'application',
            'application__campaign',
            'application__influencer',
            'application__influencer__user',
            'application__campaign__business__user',
        )
        .prefetch_related('messages')
        .order_by('-updated_at')[:5]
    )
    recent_threads = [_build_thread_data(t, user, request) for t in threads_qs]

    # ── 5. Recently joined influencers (suggested section) ───────────────────
    recent_influencers_qs = (
        InfluencerProfile.objects
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

        total_followers = sum(p.followers for p in inf.platforms.all())

        suggested_influencers.append({
            "id":              str(inf.id),
            "full_name":       inf_user.full_name,
            "city":            inf_user.city,
            "country":         inf_user.country,
            "avatar":          avatar_url,
            "bio":             inf.bio,
            "is_verified":     inf.is_verified,
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
        "stats":                 stats,
        "pending_approvals":     pending_approvals,
        "active_campaigns":      active_campaigns,
        "recent_threads":        recent_threads,
        "suggested_influencers": suggested_influencers,
    })
