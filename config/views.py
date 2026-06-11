from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings


def base_view(request):
    return render(request, 'welcome.html', {'project_name': settings.APP_NAME})


def home(request):
    # Authenticated users go straight to their dashboard
    if request.user.is_authenticated:
        if request.user.is_business:
            return redirect('enterprise_home')
        elif request.user.is_influencer:
            return redirect('influencer_home')

    categories = [
        'Mode', 'Food & Drink', 'Tech', 'Fitness', 'Beauté',
        'Voyage', 'Gaming', 'Finance', 'Éducation', 'Lifestyle',
        'Musique', 'Santé', 'Sport', 'Décoration', 'Automobile',
    ]
    featured_influencers = [
        {'name': 'Sophie M.', 'niche': 'Mode', 'followers': '120k abonnés', 'avatar': 'images/avatar-f1.jpg'},
        {'name': 'Karim D.', 'niche': 'Tech', 'followers': '85k abonnés', 'avatar': 'images/avatar-m1.jpg'},
        {'name': 'Léa R.', 'niche': 'Fitness', 'followers': '200k abonnés', 'avatar': 'images/avatar-f2.jpg'},
        {'name': 'Marc T.', 'niche': 'Food', 'followers': '60k abonnés', 'avatar': 'images/avatar-m2.jpg'},
    ]
    return render(request, 'home.html', {
        'categories': categories,
        'featured_influencers': featured_influencers,
    })


# ── Enterprise dashboard ──────────────────────────────────────────────────────

@login_required
def enterprise_home(request):
    # Non-business users get bounced to their own dashboard
    if not getattr(request.user, 'is_business', False):
        if getattr(request.user, 'is_influencer', False):
            return redirect('influencer_home')
        elif getattr(request.user, 'is_staff', False):
            pass  # Allow staff to view
        else:
            return redirect('home')

    context={}
    return render(request, 'enterprise/pages/home.html', context)


# ── Influencer dashboard ──────────────────────────────────────────────────────

@login_required
def influencer_home(request):
    # Non-influencer users get bounced to their own dashboard
    if not getattr(request.user, 'is_influencer', False):
        if getattr(request.user, 'is_business', False):
            return redirect('enterprise_home')
        elif getattr(request.user, 'is_staff', False):
            pass  # Allow staff to view
        else:
            return redirect('home')

    context={}

    return render(request, 'influencer/pages/home.html', context)


# ── Super Admin dashboard ─────────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_home(request):
    context = {}
    return render(request, 'admin_panel/pages/home.html', context)
