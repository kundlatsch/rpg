from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField  # se precisar
from django.core.validators import MinValueValidator


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
    # atributos bonus será um JSON até definirmos sistema de atributos
    attribute_bonuses = models.JSONField(default=dict, blank=True)
    # combat_skill = models.CharField(max_length=100, blank=True, null=True)
    # passive_skill = models.CharField(max_length=100, blank=True, null=True)
    # lista de materiais: [{"material_id": 1, "quantity": 2}, ...]
    recipe = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"Equipamento: {self.item.name}"

class PassiveSkill(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="passive_skills"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    trigger = models.CharField(
        max_length=100,
        help_text="ex: 'on_turn_start', 'on_receive_damage', 'every_3_turns'..."
    )

    def __str__(self):
        return f"{self.name} ({self.trigger})"

class PassiveEffect(models.Model):
    passive_skill = models.ForeignKey(
        PassiveSkill, on_delete=models.CASCADE, related_name="effects"
    )
    effect_type = models.CharField(
        max_length=50,
        help_text="ex: 'attribute_mod', 'status_effect', 'deal_damage', etc."
    )
    # Alvo (self / enemy)
    target = models.CharField(max_length=10, default="self")
    # Payload em JSON para você definir detalhes (qual atributo, quanto, duração, etc.)
    payload = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.effect_type} ({self.target})"

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
