from django.shortcuts import render, get_object_or_404, redirect
from .models import InventoryItem, Equipment, MarketListing, StoreItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from character.models import Character
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

#########################
###     INVENTORY     ###
#########################

@login_required
@require_POST
def equip_item(request):
    import json
    data = json.loads(request.body)

    item_id = data.get("item_id")
    action = data.get("action")
    character = request.user.character

    inv_item = None
    item = None
    equipment = None

    if action == "equip":
        try:
            inv_item = InventoryItem.objects.get(character=character, item_id=item_id)
            item = inv_item.item
        except InventoryItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item não está no inventário.'})

        if not hasattr(item, "equipment"):
            return JsonResponse({'success': False, 'error': 'Item não é equipamento.'})

        equipment = item.equipment

    slot_map = {
        'head': 'equipped_head',
        'necklace': 'equipped_necklace',
        'shoulders': 'equipped_shoulders',
        'chest': 'equipped_chest',
        'hands': 'equipped_hands',
        'feet': 'equipped_feet',
    }

    if action == "equip":
        slot = slot_map.get(equipment.slot)
        if not slot:
            return JsonResponse({'success': False, 'error': 'Slot inválido.'})

        current_equipped = getattr(character, slot)

        # devolve equipamento atual ao inventário
        if current_equipped:
            old_item = current_equipped.item
            inv_old, created = InventoryItem.objects.get_or_create(
                character=character,
                item=old_item,
                defaults={"quantity": 1}
            )
            if not created:
                inv_old.quantity += 1
                inv_old.save()

        # equipa o novo
        setattr(character, slot, equipment)
        character.save()

        # reduz inventário
        inv_item.quantity -= 1
        if inv_item.quantity <= 0:
            inv_item.delete()
        else:
            inv_item.save()

        return JsonResponse({'success': True})


    if action == "unequip":
        slot = None
        print("item id:", item_id)
        for s in slot_map.values():
            print(s)
            equipped_item = getattr(character, s)
            if equipped_item:
                print(equipped_item.item.name)
                print(equipped_item.item.id)
                print(type(equipped_item.item.id), type(item_id))
            else:
                print("None")
            if equipped_item and equipped_item.item.id == int(item_id):
                slot = s
                break

        if not slot:
            return JsonResponse({"success": False, "error": "Esse item não está equipado."})

        current_equipped = getattr(character, slot)

        # remove do slot
        setattr(character, slot, None)
        character.save()

        inv_item, created = InventoryItem.objects.get_or_create(
            character=character,
            item=current_equipped.item,
            defaults={"quantity": 1}
        )
        if not created:
            inv_item.quantity += 1
            inv_item.save()

        return JsonResponse({"success": True, "message": "Item removido e devolvido ao inventário."})

    return JsonResponse({'success': False, 'error': 'Ação inválida.'})


@login_required
def inventory_view(request):
    character = request.user.character  # porque você fez OneToOne com User
    inventory = InventoryItem.objects.filter(character=character).select_related("item")

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

#########################
###       MARKET      ###
#########################

@login_required
@require_POST
def sell_item(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    item_id = data.get("item_id")
    quantity = data.get("quantity")
    price = data.get("price")

    if not all([item_id, quantity, price]):
        return JsonResponse({"success": False, "error": "Parâmetros faltando"}, status=400)

    if quantity <= 0 or price <= 0:
        return JsonResponse({"success": False, "error": "Quantidade e preço devem ser > 0"}, status=400)

    character = request.user.character

    # Verifica se o item está no inventário
    try:
        inv_item = InventoryItem.objects.get(character=character, item_id=item_id)
    except InventoryItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item não está no inventário"}, status=400)

    # Verifica se há quantidade suficiente
    if inv_item.quantity < quantity:
        return JsonResponse({"success": False, "error": "Quantidade insuficiente no inventário"}, status=400)

    # Cria o anúncio
    listing = MarketListing.objects.create(
        seller=character,
        item=inv_item.item,
        price=price,
        quantity=quantity
    )

    # Remove a quantidade do inventário
    inv_item.quantity -= quantity
    if inv_item.quantity <= 0:
        inv_item.delete()
    else:
        inv_item.save()

    return JsonResponse({
        "success": True,
        "message": "Item colocado à venda com sucesso!",
        "listing_id": listing.id
    })

@login_required
@require_POST
def cancel_listing(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    listing_id = data.get("listing_id")

    if not listing_id:
        return JsonResponse({"success": False, "error": "listing_id faltando"}, status=400)

    try:
        listing = MarketListing.objects.get(id=listing_id)
    except MarketListing.DoesNotExist:
        return JsonResponse({"success": False, "error": "Anúncio não encontrado"}, status=404)

    # Apenas o vendedor pode cancelar
    if listing.seller != request.user:
        return JsonResponse({"success": False, "error": "Você não pode deletar este anúncio"}, status=403)

    # devolve ao inventário
    inv_item, created = InventoryItem.objects.get_or_create(
        character=request.user.character,
        item=listing.item,
        defaults={"quantity": listing.quantity}
    )
    if not created:
        inv_item.quantity += listing.quantity
        inv_item.save()

    listing.delete()

    return JsonResponse({"success": True, "message": "Anúncio removido e itens devolvidos ao inventário."})


@login_required
@require_POST
def buy_item(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    listing_id = data.get("listing_id")
    quantity = data.get("quantity")

    if not listing_id or not quantity:
        return JsonResponse({"success": False, "error": "Parâmetros faltando"}, status=400)

    if quantity <= 0:
        return JsonResponse({"success": False, "error": "Quantidade deve ser > 0"}, status=400)

    try:
        listing = MarketListing.objects.get(id=listing_id)
    except MarketListing.DoesNotExist:
        return JsonResponse({"success": False, "error": "Anúncio não encontrado"}, status=404)

    buyer = request.user
    seller = listing.seller
    character = buyer.character

    # não pode comprar de si mesmo
    if seller == buyer:
        return JsonResponse({"success": False, "error": "Você não pode comprar seu próprio anúncio"}, status=400)

    # quantidade disponível
    if listing.quantity < quantity:
        return JsonResponse({"success": False, "error": "Quantidade insuficiente no anúncio"}, status=400)

    total_price = listing.price * quantity

    # verifica dinheiro
    if character.gold < total_price:
        return JsonResponse({"success": False, "error": "Ouro insuficiente"}, status=400)

    # desconta ouro do comprador
    character.gold -= total_price
    character.save()

    # paga o vendedor
    seller.character.gold += total_price
    seller.character.save()

    # entrega itens ao comprador
    inv_item, created = InventoryItem.objects.get_or_create(
        character=character,
        item=listing.item,
        defaults={"quantity": quantity}
    )
    if not created:
        inv_item.quantity += quantity
        inv_item.save()

    # atualiza anúncio
    listing.quantity -= quantity
    if listing.quantity <= 0:
        listing.delete()
    else:
        listing.save()

    return JsonResponse({"success": True, "message": "Compra realizada com sucesso!"})


@login_required
def market_view(request):
    character = request.user.character

    # inventário
    inventory = InventoryItem.objects.filter(character=character).select_related("item")

    # separa por tipo
    user_materials = [inv for inv in inventory if inv.item.item_type == "material"]
    user_equipment = [inv for inv in inventory if inv.item.item_type == "equipment"]
    user_consumables = [inv for inv in inventory if inv.item.item_type == "consumable"]

    # mercado
    listings = MarketListing.objects.all()

    # separa por tipo
    market_materials = [i for i in listings if i.item.item_type == "material"]
    market_equipment = [i for i in listings if i.item.item_type == "equipment"]
    market_consumables = [i for i in listings if i.item.item_type == "consumable"]

    return render(
        request,
        "items/market.html",
        {
            "character": character,
            "user_materials": user_materials,
            "user_equipment": user_equipment,
            "user_consumables": user_consumables,
            "market_materials": market_materials,
            "market_equipment": market_equipment,
            "market_consumables": market_consumables,
        },
    )

#########################
###       STORE        ###
#########################

@login_required
def store_view(request):
    """
    Página da loja NPC
    """
    store_items = StoreItem.objects.select_related("item").all()
    character = request.user.character

    inventory = InventoryItem.objects.filter(character=character).select_related("item")

    return render(
        request,
        "items/store.html",
        {
            "character": character,
            "store_items": store_items,
            "inventory": inventory,
        },
    )


@login_required
@require_POST
def store_buy(request):
    """
    Comprar item da loja NPC
    """
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    store_item_id = data.get("store_item_id")
    quantity = data.get("quantity")

    if not store_item_id or not quantity:
        return JsonResponse({"success": False, "error": "Dados incompletos"}, status=400)

    try:
        store_item = StoreItem.objects.select_related("item").get(id=store_item_id)
    except StoreItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item inexistente"}, status=404)

    character = request.user.character
    total_cost = store_item.buy_price * quantity

    if character.gold < total_cost:
        return JsonResponse({"success": False, "error": "Ouro insuficiente"}, status=400)

    # Se a loja não tem estoque infinito, verifica
    if not store_item.unlimited and store_item.stock < quantity:
        return JsonResponse({"success": False, "error": "Loja sem estoque suficiente"}, status=400)

    # Comprar
    character.gold -= total_cost
    character.save()

    # Dar item ao personagem
    inv, created = InventoryItem.objects.get_or_create(
        character=character,
        item=store_item.item,
        defaults={"quantity": 0},
    )
    inv.quantity += quantity
    inv.save()

    # Reduz estoque da loja
    if not store_item.unlimited:
        store_item.stock -= quantity
        store_item.save()

    return JsonResponse({"success": True, "message": "Compra realizada!"})


@login_required
@require_POST
def store_sell(request):
    try:
        data = json.loads(request.body)
        item_id = data.get("item_id")
        quantity = data.get("quantity")
    except:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    if not item_id or not quantity:
        return JsonResponse({"success": False, "error": "Parâmetros faltando"}, status=400)

    if quantity <= 0:
        return JsonResponse({"success": False, "error": "Quantidade inválida"}, status=400)

    character = request.user.character

    # Item no inventário
    try:
        inv_item = InventoryItem.objects.get(character=character, item_id=item_id)
    except InventoryItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item não existe no inventário"}, status=400)

    if inv_item.quantity < quantity:
        return JsonResponse({"success": False, "error": "Quantidade insuficiente"}, status=400)

    # Calcula preço
    item_price = inv_item.item.sell_price
    total_gold = item_price * quantity

    # Dá o ouro
    character.gold += total_gold
    character.save()

    # Remove item
    inv_item.quantity -= quantity
    if inv_item.quantity <= 0:
        inv_item.delete()
    else:
        inv_item.save()

    return JsonResponse({
        "success": True,
        "message": f"Você vendeu {quantity}x {inv_item.item.name} por {total_gold} gold!",
        "gold_gained": total_gold
    })
