from django.core.management.base import BaseCommand
from items.models import Item, ItemType, ItemRarity, Equipment, Consumable, Material


class Command(BaseCommand):
    help = "Popula o banco de dados com itens de teste"

    def handle(self, *args, **options):
        self.stdout.write("Criando itens de teste...")

        # Limpa os itens antigos
        Material.objects.all().delete()
        Consumable.objects.all().delete()
        Equipment.objects.all().delete()
        Item.objects.all().delete()

        # Materiais
        madeira = Item.objects.create(
            name="Madeira",
            description="Um pedaço de madeira.",
            emoji="🪵",
            drop_chance=0.5,
            rarity=ItemRarity.COMMON,
            item_type=ItemType.MATERIAL,
        )
        Material.objects.create(item=madeira)

        ferro = Item.objects.create(
            name="Minério de Ferro",
            description="Minério bruto de ferro.",
            emoji="⛏️",
            drop_chance=0.3,
            rarity=ItemRarity.RARE,
            item_type=ItemType.MATERIAL,
        )
        Material.objects.create(item=ferro)

        # Equipamento
        espada = Item.objects.create(
            name="Espada de Treinamento",
            description="Uma espada simples para iniciantes.",
            emoji="🗡️",
            drop_chance=0.1,
            rarity=ItemRarity.COMMON,
            item_type=ItemType.EQUIPMENT,
        )
        Equipment.objects.create(
            item=espada,
            min_level=1,
            attribute_bonuses={"strength": 2},
        )

        arco = Item.objects.create(
            name="Arco Curto",
            description="Um arco curto para arqueiros iniciantes.",
            emoji="🏹",
            drop_chance=0.1,
            rarity=ItemRarity.COMMON,
            item_type=ItemType.EQUIPMENT,
        )
        Equipment.objects.create(
            item=arco,
            min_level=1,
            attribute_bonuses={"dexterity": 2},
        )

        # Consumíveis
        pocao = Item.objects.create(
            name="Poção de Cura",
            description="Recupera 50 de vida.",
            emoji="🧪",
            drop_chance=0.2,
            rarity=ItemRarity.COMMON,
            item_type=ItemType.CONSUMABLE,
        )
        Consumable.objects.create(
            item=pocao,
            min_level=1,
            affected_attributes=["hp"],
            attribute_bonuses={"hp": +50},
        )

        self.stdout.write(self.style.SUCCESS("Itens de teste criados com sucesso!"))
