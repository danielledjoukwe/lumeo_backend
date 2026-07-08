from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from profiles.models import BusinessProfile, Category
from campaigns.models import Campaign


def _get_business_or_redirect(request):
    """
    Returns the BusinessProfile for the logged-in user, or None if the user
    is not a business (the caller should redirect in that case).
    """
    if not getattr(request.user, 'is_business', False):
        return None
    profile, _ = BusinessProfile.objects.get_or_create(user=request.user)
    return profile


# ── List ─────────────────────────────────────────────────────────────────────

@login_required
def campaign_list(request):
    """All campaigns belonging to the logged-in business."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaigns = Campaign.objects.filter(business=business)

    # Status filter from query-string  (?status=draft / open / ...)
    status_filter = request.GET.get('status', '')
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    all_campaigns = Campaign.objects.filter(business=business)
    
    # Pagination
    paginator = Paginator(campaigns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj':      page_obj,
        'status_filter': status_filter,
        'campaign_count': all_campaigns.count(),
    }
    return render(request, 'enterprise/pages/campagne/list.html', context)


# ── Create ────────────────────────────────────────────────────────────────────

@login_required
def campaign_create(request):
    """Create a new campaign (saved as draft by default)."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        title              = request.POST.get('title', '').strip()
        description        = request.POST.get('description', '').strip()
        deliverables_brief = request.POST.get('deliverables_brief', '').strip()
        budget             = request.POST.get('budget', '').strip()
        duration           = request.POST.get('duration', '').strip()
        deadline           = request.POST.get('deadline', '').strip()
        max_influencers    = request.POST.get('max_influencers', '1').strip()
        category_ids       = request.POST.getlist('target_categories')
        # Explicit publish: only 'open' or 'draft' allowed on create
        status             = request.POST.get('status', 'draft')
        if status not in ('draft', 'open'):
            status = 'draft'

        # Basic validation
        errors = []
        if not title:
            errors.append("Le titre est obligatoire.")
        if not description:
            errors.append("La description est obligatoire.")
        if not deliverables_brief:
            errors.append("Le brief des livrables est obligatoire.")
        if not budget:
            errors.append("Le budget est obligatoire.")
        if not deadline:
            errors.append("La date limite est obligatoire.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            campaign = Campaign.objects.create(
                business           = business,
                title              = title,
                description        = description,
                deliverables_brief = deliverables_brief,
                budget             = budget,
                duration           = duration,
                deadline           = deadline,
                max_influencers    = int(max_influencers) if max_influencers.isdigit() else 1,
                status             = status,
            )
            if category_ids:
                campaign.target_categories.set(
                    Category.objects.filter(id__in=category_ids)
                )
            messages.success(request, "Campagne créée avec succès.")
            return redirect('campaign_detail', pk=campaign.pk)

    context = {
        'categories': categories,
        'campaign_count': Campaign.objects.filter(business=business).count(),
    }
    return render(request, 'enterprise/pages/campagne/create.html', context)


# ── Detail ────────────────────────────────────────────────────────────────────

@login_required
def campaign_detail(request, pk):
    """Read-only detail view of a single campaign."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    context = {
        'campaign': campaign,
        'campaign_count': Campaign.objects.filter(business=business).count(),
    }
    return render(request, 'enterprise/pages/campagne/detail.html', context)


# ── Edit ──────────────────────────────────────────────────────────────────────

@login_required
def campaign_edit(request, pk):
    """Edit an existing campaign."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaign   = get_object_or_404(Campaign, pk=pk, business=business)
    categories = Category.objects.all().order_by('name')
    selected_category_ids = set(
        str(c.id) for c in campaign.target_categories.all()
    )

    if request.method == 'POST':
        title              = request.POST.get('title', '').strip()
        description        = request.POST.get('description', '').strip()
        deliverables_brief = request.POST.get('deliverables_brief', '').strip()
        budget             = request.POST.get('budget', '').strip()
        duration           = request.POST.get('duration', '').strip()
        deadline           = request.POST.get('deadline', '').strip()
        max_influencers    = request.POST.get('max_influencers', '1').strip()
        category_ids       = request.POST.getlist('target_categories')
        status             = request.POST.get('status', campaign.status)
        if status not in dict(Campaign.STATUS_CHOICES):
            status = campaign.status

        errors = []
        if not title:
            errors.append("Le titre est obligatoire.")
        if not description:
            errors.append("La description est obligatoire.")
        if not deliverables_brief:
            errors.append("Le brief des livrables est obligatoire.")
        if not budget:
            errors.append("Le budget est obligatoire.")
        if not deadline:
            errors.append("La date limite est obligatoire.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            campaign.title              = title
            campaign.description        = description
            campaign.deliverables_brief = deliverables_brief
            campaign.budget             = budget
            campaign.duration           = duration
            campaign.deadline           = deadline
            campaign.max_influencers    = int(max_influencers) if max_influencers.isdigit() else 1
            campaign.status             = status
            campaign.save()
            campaign.target_categories.set(
                Category.objects.filter(id__in=category_ids)
            )
            messages.success(request, "Campagne mise à jour avec succès.")
            return redirect('campaign_detail', pk=campaign.pk)

    context = {
        'campaign':              campaign,
        'categories':            categories,
        'selected_category_ids': selected_category_ids,
        'status_choices':        Campaign.STATUS_CHOICES,
        'campaign_count':        Campaign.objects.filter(business=business).count(),
    }
    return render(request, 'enterprise/pages/campagne/edit.html', context)


# ── Delete ────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def campaign_delete(request, pk):
    """Delete a campaign (POST only)."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaign = get_object_or_404(Campaign, pk=pk, business=business)
    campaign.delete()
    messages.success(request, f"La campagne « {campaign.title} » a été supprimée.")
    return redirect('campaign_list')


# ── Publish / Unpublish (status toggles) ─────────────────────────────────────

@login_required
@require_POST
def campaign_publish(request, pk):
    """Publish a draft campaign (set status to 'open')."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaign = get_object_or_404(Campaign, pk=pk, business=business)
    if campaign.status == 'draft':
        campaign.status = 'open'
        campaign.save(update_fields=['status'])
        messages.success(request, "Campagne publiée — les influenceurs peuvent maintenant postuler.")
    return redirect('campaign_detail', pk=campaign.pk)


@login_required
@require_POST
def campaign_unpublish(request, pk):
    """Revert an open campaign back to draft."""
    business = _get_business_or_redirect(request)
    if business is None:
        return redirect('home')

    campaign = get_object_or_404(Campaign, pk=pk, business=business)
    if campaign.status == 'open':
        campaign.status = 'draft'
        campaign.save(update_fields=['status'])
        messages.success(request, "Campagne repassée en brouillon.")
    return redirect('campaign_detail', pk=campaign.pk)
