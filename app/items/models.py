from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField  # se precisar
from django.core.validators import MinValueValidator

from .constants import ATTRIBUTE_LABELS, TRIGGER_LABELS, RECIPE_LABELS, STAT_LABELS, ITEM_RARITY_BASE_PRICE, ITEM_PRICE_MULTIPLIER
from .utils import SafeStats

class ItemType(models.TextChoices):
    MATERIAL = "material", "Material"
    EQUIPMENT = "equipment", "Equipamento"
    CONSUMABLE = "consumable", "Consumível"


class ItemRarity(models.TextChoices):
    COMMON = "common", "Comum"
    RARE = "rare", "Raro"
    EPIC = "epic", "Épico"
    LEGENDARY = "legendary", "Lendário"


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    emoji = models.CharField(max_length=5, help_text="Ex: 🗡️ ou 🪵")
    drop_chance = models.FloatField(default=0.0)
    rarity = models.CharField(
        max_length=20, choices=ItemRarity.choices, default=ItemRarity.COMMON
    )
    item_type = models.CharField(max_length=20, choices=ItemType.choices)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"

    def __str__(self):
        return f"{self.emoji} {self.name}"
    
    @property
    def sell_price(self):
        base = ITEM_RARITY_BASE_PRICE.get(self.rarity, 10)
        mult = ITEM_PRICE_MULTIPLIER.get(self.item_type, 1)
        return base * mult

class EquipmentSlot(models.TextChoices):
    HEAD = "head", "Cabeça"
    NECK = "necklace", "Colar"
    SHOULDERS = "shoulders", "Ombros"
    CHEST = "chest", "Tronco"
    HANDS = "hands", "Mãos"
    FEET = "feet", "Pés"

class Equipment(models.Model):
    item = models.OneToOneField(
        Item, on_delete=models.CASCADE, related_name="equipment"
    )

    min_level = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    slot = models.CharField(
        max_length=20, choices=EquipmentSlot.choices, default=EquipmentSlot.HEAD
    )

    recipe = models.JSONField(default=list, blank=True, null=True)

    attribute_bonuses = models.JSONField(default=dict, blank=True)

    stats = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Exemplo:
        {
            "attack": {
                "type": "physical",
                "style": "slash",
                "value": 10
            },
            "defense": {
                "type": "magic",
                "weakness": "slash",
                "value": 5
            }
        }
        """
    )

    passive_skill = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Exemplo:
        {
            "name": "Espírito Guardião",
            "trigger": "on_turn_start",
            "description": "Flavor text",
            "cost": 10,
            "effects": [
                {"type": "attribute_mod", "target": "self", "payload": {"attr": "strength", "value": 2}},
                {"type": "status_effect", "target": "enemy", "payload": {"status": "burn", "duration": 2}}
            ]
        }
        """
    )

    @property
    def formatted_passive_skill_effects(self):
        """Retorna uma string formatada com os efeitos da habilidade passiva (com tradução)."""
        if not self.passive_skill or 'effects' not in self.passive_skill:
            return ""

        effects = self.passive_skill['effects']
        if not effects:
            return ""
        
        effect_strings = []
        for effect in effects:
            effect_type = effect.get('type')
            target = effect.get('target', 'self')
            cost = effect.get("cost", 0)
            payload = effect.get('payload', {})

            def translate_attr(attr_key: str) -> str:
                if not attr_key:
                    return ""
                return ATTRIBUTE_LABELS.get(attr_key, attr_key.replace("_", " ").title())

            if effect_type == 'attribute_mod':
                attr_key = payload.get('attr', '')
                attr = translate_attr(attr_key)
                value = payload.get('value', 0)
                sign = '+' if value > 0 else ''
                effect_str = f"{sign}{value} {attr}"

            elif effect_type == 'status_effect':
                status = payload.get('status', '').title()
                duration = payload.get('duration', 0)
                effect_str = f"Aplica {status} por {duration} turno(s)"

            elif effect_type == 'heal':
                amount = payload.get('amount', 0) or payload.get('value', 0)
                effect_str = f"Cura {amount} de vida"

            elif effect_type == 'damage':
                amount = payload.get('amount', 0) or payload.get('value', 0)
                damage_type = payload.get('damage_type', '').title()
                effect_str = f"Causa {amount} de dano {damage_type}".strip()

            elif effect_type == 'defense_buff':
                amount = payload.get('amount', 0) or payload.get('value', 0)
                effect_str = f"+{amount} de Defesa"

            else:
                # fallback
                effect_str = f"{effect_type}: {payload}"

            if target != 'self':
                target_map = {
                    "enemy": "inimigo",
                    "ally": "aliado",
                }
                target_str = target_map.get(target, target)
                effect_str += f" no {target_str}"

            effect_strings.append(effect_str)

        return ", ".join(effect_strings)
    


    @property
    def formatted_equipment_stats(self) -> str:
        """
        Converte o JSONField 'stats' em uma string amigável em português.
        """
        def translate(key: str) -> str:
            return STAT_LABELS.get(key, key.replace("_", " "))
        
        stats = self.stats
        if not stats:
            return ""

        lines = []

        for key, data in stats.items():
            if not isinstance(data, dict):
                continue

            stat_name = translate(key).capitalize()  # ex: defense → Defesa
            line = stat_name

            value = data.get("value")
            stype = data.get("type")
            style = data.get("style")
            weakness = data.get("weakness")

            desc_parts = []

            if stype:
                line += " " + translate(stype)
            line += ":"
            if value:
                line += " +" + str(value)
            if style:
                line += " " + translate(style)
            if weakness:
                line += " " + "(fraco contra " + translate(weakness) + ")"

            lines.append(line)

        return "\n".join(lines)


    @property
    def attribute_bonuses_strings(self):
        translated = {}
        for key, value in self.attribute_bonuses.items():
            label = ATTRIBUTE_LABELS.get(key, key.replace("_", " ").title())
            translated[label] = value
        return translated

    def __str__(self):
        return f"Equipamento: {self.item.name}"
    
    @property
    def recipe_strings(self):
        if not self.recipe:
            return {}

        translated = {}
        for key, value in self.recipe.items():
            label = RECIPE_LABELS.get(key, key.replace("_", " ").title())
            translated[label] = value

        return translated
    
    @property
    def trigger_string(self):
        if not self.passive_skill:
            return ""
        cost = self.passive_skill.get("cost", 0)
        trigger_key = self.passive_skill.get("trigger", "")
        trigger_label = TRIGGER_LABELS.get(trigger_key, trigger_key.replace("_", " ").title())
        return f"{trigger_label} ({cost} PM)"
    
    @property
    def parsed_stats(self):
        return SafeStats(self.stats)

class Consumable(models.Model):
    item = models.OneToOneField(
        Item, on_delete=models.CASCADE, related_name="consumable"
    )

    min_level = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    affected_attributes = models.JSONField(
        blank=True, null=True
    )  # ["strength", "agility"]
    attribute_bonuses = models.JSONField(
        blank=True, null=True
    )  # {"strength": +5, "agility": +1}
    crafting_recipe = models.JSONField(
        blank=True, null=True
    )  # [{"item_id":1, "qty":5}, ...]

    def __str__(self):
        return f"Consumível: {self.item.name}"


class Material(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="material")

    crafting_recipe = models.JSONField(
        blank=True, null=True
    )  # [{"item_id":1, "qty":5}, ...]

    def __str__(self):
        return f"Material: {self.item.name}"


class InventoryItem(models.Model):
    character = models.ForeignKey(
        "character.Character", on_delete=models.CASCADE, related_name="inventory"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("character", "item")
        verbose_name = "Item do Inventário"
        verbose_name_plural = "Inventário"

    def __str__(self):
        return f"{self.character.name} - {self.quantity}x {self.item.name}"


class MarketListing(models.Model):
    seller = models.ForeignKey(
        "character.Character", on_delete=models.CASCADE, related_name="listings"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.seller.username} vende {self.quantity}x {self.item}"


class StoreItem(models.Model):
    """
    Itens disponíveis na loja do NPC.
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    buy_price = models.PositiveIntegerField()
    unlimited = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.item.name} (Loja)"
