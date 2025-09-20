from django.shortcuts import render
from .models import InventoryItem
from django.contrib.auth.decorators import login_required

@login_required
def inventory_view(request):
    character = request.user.character  # porque você fez OneToOne com User
    inventory = InventoryItem.objects.filter(character=character).select_related("item")

    # separa por tipo
    materials = [inv for inv in inventory if inv.item.item_type == "material"]
    equipment = [inv for inv in inventory if inv.item.item_type == "equipment"]
    consumables = [inv for inv in inventory if inv.item.item_type == "consumable"]

    return render(
        request,
        "items/inventory.html",
        {
            "character": character,
            "materials": materials,
            "equipment": equipment,
            "consumables": consumables,
        },
    )
