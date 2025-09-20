import random
from django.core.management.base import BaseCommand
from character.models import Character
from items.models import Item, InventoryItem


class Command(BaseCommand):
    help = "Popula o inventário dos personagens com itens de teste"

    def handle(self, *args, **options):
        characters = Character.objects.all()
        items = list(Item.objects.all())

        if not characters.exists():
            self.stdout.write(self.style.ERROR("Nenhum personagem encontrado!"))
            return

        if not items:
            self.stdout.write(self.style.ERROR("Nenhum item encontrado! Rode seed_items primeiro."))
            return

        for char in characters:
            self.stdout.write(f"Populando inventário de {char.name}...")

            # Limpa inventário antigo
            InventoryItem.objects.filter(character=char).delete()

            # Adiciona de 3 a 5 itens aleatórios
            # sample_items = random.sample(items, k=min(5, len(items)))
            for item in items:
                qty = random.randint(1, 5)  # quantidade aleatória
                InventoryItem.objects.create(character=char, item=item, quantity=qty)
                self.stdout.write(f"  {qty}x {item.name}")

        self.stdout.write(self.style.SUCCESS("Inventários de teste populados com sucesso!"))
