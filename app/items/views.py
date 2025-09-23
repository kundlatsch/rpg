from django.shortcuts import render
from .models import InventoryItem
from django.contrib.auth.decorators import login_required

@login_required
def inventory_view(request):
    character = request.user.character  # porque você fez OneToOne com User
    inventory = InventoryItem.objects.filter(character=character).select_related("item")

    slots = [
        character.equipped_head,
        character.equipped_necklace,
        character.equipped_shoulders,
        character.equipped_chest,
        character.equipped_hands,
        character.equipped_feet,
    ]

    slots = [equip.item for equip in slots if equip]
    inventory = [inv for inv in inventory if ((inv.item not in slots) or (inv.quantity > 1))]

    # separa por tipo
    materials = [inv for inv in inventory if inv.item.item_type == "material"]
    equipment = [inv for inv in inventory if inv.item.item_type == "equipment"]
    consumables = [inv for inv in inventory if inv.item.item_type == "consumable"]

    upper_slots = [
        {"name": "Cabeça", "icon": "👑", "equipment": character.equipped_head},
        {"name": "Colar", "icon": "📿", "equipment": character.equipped_necklace},
        {"name": "Ombro", "icon": "🎗️", "equipment": character.equipped_shoulders},
    ]
    lower_slots = [
        {"name": "Tronco", "icon": "🦺", "equipment": character.equipped_chest},
        {"name": "Mãos", "icon": "🧤", "equipment": character.equipped_hands},
        {"name": "Pés", "icon": "👞", "equipment": character.equipped_feet},
    ]

    return render(
        request,
        "items/inventory.html",
        {
            "character": character,
            "materials": materials,
            "equipment": equipment,
            "consumables": consumables,
            "upper_slots": upper_slots,
            "lower_slots": lower_slots,
        },
    )
