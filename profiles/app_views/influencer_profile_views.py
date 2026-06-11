from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.contrib.auth import get_user_model
from ..models import Category, InfluencerProfile, SocialPlatform


def _get_or_create_profile(user):
    profile, _ = InfluencerProfile.objects.get_or_create(user=user)
    return profile


@login_required
def influencer_profile(request):
    profile = _get_or_create_profile(request.user)

    if request.method == 'POST':
        user = request.user

        # ── User fields ──────────────────────────────────────
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.phone      = request.POST.get('phone', '').strip() or None
        user.city       = request.POST.get('city', '').strip() or None
        user.country    = request.POST.get('country', '').strip() or None

        username = request.POST.get('username', '').strip() or None
        if username and username != user.username:
            
            User = get_user_model()
            if User.objects.exclude(pk=user.pk).filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                return redirect('influencer_profile')
        user.username = username

        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']

        user.save()

        # ── Influencer bio ───────────────────────────────────
        profile.bio = request.POST.get('bio', '').strip()

        # ── Categories (max 5) ───────────────────────────────
        category_ids = request.POST.getlist('categories')[:5]
        profile.save()
        profile.categories.set(Category.objects.filter(id__in=category_ids))

        # ── Social platforms ─────────────────────────────────
        platform_ids      = request.POST.getlist('platform_id[]')
        platform_names    = request.POST.getlist('platform_name[]')
        platform_urls     = request.POST.getlist('platform_url[]')
        platform_followers = request.POST.getlist('platform_followers[]')

        submitted_ids = set()

        for pid, name, url, followers in zip(platform_ids, platform_names, platform_urls, platform_followers):
            url = url.strip()
            if not url:
                continue
            try:
                followers_int = int(followers) if followers else 0
            except ValueError:
                followers_int = 0

            if pid:
                # Update existing
                SocialPlatform.objects.filter(id=pid, profile=profile).update(
                    platform=name,
                    profile_url=url,
                    followers=followers_int,
                )
                submitted_ids.add(pid)
            else:
                # Create new — skip duplicates silently
                obj, _ = SocialPlatform.objects.get_or_create(
                    profile=profile,
                    platform=name,
                    defaults={'profile_url': url, 'followers': followers_int},
                )
                if not _:
                    obj.profile_url = url
                    obj.followers = followers_int
                    obj.save()
                submitted_ids.add(str(obj.id))

        # Delete removed platforms
        profile.platforms.exclude(id__in=[i for i in submitted_ids if i]).delete()

        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('influencer_profile')

    # ── GET ──────────────────────────────────────────────────
    return render(request, 'influencer/pages/profile.html', {
        'profile':             profile,
        'platforms':           profile.platforms.all().order_by('platform'),
        'all_categories':      Category.objects.all(),
        'selected_categories': list(profile.categories.all()),
    })


