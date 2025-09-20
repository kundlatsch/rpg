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

        # Equipamentos de teste (10)
        equipamentos = [
            ("Espada de Treinamento", "Uma espada simples para iniciantes.", "🗡️", {"strength": 2}),
            ("Arco Curto", "Um arco curto para arqueiros iniciantes.", "🏹", {"dexterity": 2}),
            ("Machado de Madeira", "Um machado leve de madeira.", "🪓", {"strength": 1}),
            ("Cajado Rústico", "Um cajado para magos iniciantes.", "🪄", {"intelligence": 2}),
            ("Escudo Pequeno", "Um escudo leve para defesa básica.", "🛡️", {"constitution": 1}),
            ("Elmo de Couro", "Proteção básica para a cabeça.", "🥽", {"constitution": 1}),
            ("Armadura de Couro", "Proteção básica para o corpo.", "🥋", {"constitution": 2}),
            ("Luvas de Couro", "Luvas reforçadas para mais destreza.", "🧤", {"dexterity": 1}),
            ("Botas Rápidas", "Botas que aumentam agilidade.", "👢", {"agility": 1}),
            ("Anel do Iniciante", "Um anel simples que aumenta energia.", "💍", {"energy": 5}),
        ]

        for nome, desc, emoji, bonus in equipamentos:
            item = Item.objects.create(
                name=nome,
                description=desc,
                emoji=emoji,
                drop_chance=0.1,
                rarity=ItemRarity.COMMON,
                item_type=ItemType.EQUIPMENT,
            )
            Equipment.objects.create(item=item, min_level=1, attribute_bonuses=bonus)

        # Consumível
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
