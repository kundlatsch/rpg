from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InventoryItem

@login_required
def inventory_view(request):
    character = request.user.character
    all_items = InventoryItem.objects.filter(character=character).select_related('item')
    return render(request, 'inventory.html', {
        'character': character,
        'all_items': all_items
    })
