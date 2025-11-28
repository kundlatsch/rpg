from items.models import Item, Equipment, ItemType, ItemRarity, EquipmentSlot
import random

def create_mock_equipment(slot):
    """Cria um equipamento falso sem salvar no banco."""

    # Criar Item sem salvar
    item = Item(
        name=f"Mock {slot.title()}",
        description=f"Equipamento falso para slot {slot}",
        emoji="🛡️",
        drop_chance=0.0,
        rarity=ItemRarity.COMMON,
        item_type=ItemType.EQUIPMENT,
    )

    # Criar Equipment sem salvar
    equip = Equipment(
        item=item,
        min_level=1,
        slot=slot,
        attribute_bonuses={},
        stats={
            "attack": {
                "type": "physical",
                "style": "slash",
                "value": random.randint(0, 4),
            },
            "defense": {
                "type": "physical",
                "weakness": None,
                "value": random.randint(1, 5),
            }
        },
    )

    return equip
