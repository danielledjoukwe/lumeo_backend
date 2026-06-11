from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from profiles.models import BusinessProfile

@login_required
def enterprise_profile(request):
    """
    View for viewing and editing the Business Profile.
    """
    # Ensure user is a business
    if not getattr(request.user, 'is_business', False):
        if getattr(request.user, 'is_influencer', False):
            return redirect('influencer_profile')
        return redirect('home')

    # Get or create the profile
    profile, created = BusinessProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Simple processing
        company_name = request.POST.get('company_name', '').strip()
        industry = request.POST.get('industry', '').strip()
        website = request.POST.get('website', '').strip()
        description = request.POST.get('description', '').strip()

        # Update User fields (first_name, last_name, email)
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if first_name or last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

        # Update Profile fields
        profile.company_name = company_name
        profile.industry = industry
        profile.website = website
        profile.description = description
        profile.save()

        messages.success(request, "Profil entreprise mis à jour avec succès.")
        return redirect('enterprise_profile')

    context = {
        'profile': profile,
    }
    return render(request, 'enterprise/pages/profile.html', context)
