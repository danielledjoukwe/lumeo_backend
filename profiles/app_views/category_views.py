from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..models import Category

@login_required
@require_GET
def category_search(request):
    """AJAX endpoint — returns JSON list of categories matching `q`."""
    q = request.GET.get('q', '').strip()
    qs = Category.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    data = [{'id': str(c.id), 'name': c.name} for c in qs[:20]]
    return JsonResponse({'results': data})