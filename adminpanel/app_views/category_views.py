from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from profiles.models import Category


def staff_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff)(view_func))


# ── Categories ────────────────────────────────────────────────────────────────

@staff_required
def manage_categories(request):
    categories = Category.objects.all()
    return render(request, 'admin_panel/pages/categories/categories.html', {
        'categories': categories,
    })


@staff_required
def add_category(request):
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Le nom est obligatoire.')
            return render(request, 'admin_panel/pages/categories/add-categories.html', {
                'form_data': request.POST,
            })

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Une catégorie nommée « {name} » existe déjà.')
            return render(request, 'admin_panel/pages/categories/add-categories.html', {
                'form_data': request.POST,
            })

        Category.objects.create(name=name, description=description)
        messages.success(request, f'Catégorie « {name} » créée avec succès.')
        return redirect('manage-categories')

    return render(request, 'admin_panel/pages/categories/add-categories.html')


@staff_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Le nom est obligatoire.')
            return render(request, 'admin_panel/pages/categories/edit-categories.html', {
                'category': category,
            })

        if Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Une catégorie nommée « {name} » existe déjà.')
            return render(request, 'admin_panel/pages/categories/edit-categories.html', {
                'category': category,
            })

        category.name        = name
        category.description = description
        category.save()

        messages.success(request, f'Catégorie « {name} » mise à jour avec succès.')
        return redirect('manage-categories')

    return render(request, 'admin_panel/pages/categories/edit-categories.html', {
        'category': category,
    })


@staff_required
def delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        name = category.name
        category.delete()
        messages.success(request, f'Catégorie « {name} » supprimée.')
    return redirect('manage-categories')
