from django.db import models
from django.contrib.auth.models import User

from .constants import SLOT_WEAKNESS_MULTIPLIER

class CharactersConfig(models.Model):
    # Progressão de nível
    level_growth_rate = models.FloatField(default=1.5)  # 50% mais difícil a cada nível

class Character(models.Model):

    CHARACTER_TYPES = [
        ("player", "Player"),
        ("npc", "NPC"),
        ("monster", "Monster"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=CHARACTER_TYPES,
        default="player",
    )
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=5, default="😃")
    gold = models.IntegerField(default=0)

    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    max_exp = models.IntegerField(default=100)
    attribute_points = models.PositiveIntegerField(default=0)

    max_hp = models.IntegerField(default=100)
    hp = models.IntegerField(default=100)
    max_mana = models.IntegerField(default=50)
    mana = models.IntegerField(default=50)
    max_stamina = models.IntegerField(default=100)
    stamina = models.IntegerField(default=100)
    training_start = models.DateTimeField(null=True, blank=True)
    resting_start = models.DateTimeField(null=True, blank=True)

    # --- ATRIBUTOS PRIMÁRIOS ---
    strength = models.PositiveIntegerField(default=1)       # Força
    dexterity = models.PositiveIntegerField(default=1)      # Destreza
    arcane = models.PositiveIntegerField(default=1)         # Arcano
    constitution = models.PositiveIntegerField(default=1)   # Constituição
    courage = models.PositiveIntegerField(default=1)        # Coragem
    luck = models.PositiveIntegerField(default=1)           # Sorte

    # --- SLOTS DE EQUIPAMENTOS ---
    equipped_head = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    equipped_necklace = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    equipped_shoulders = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    equipped_chest = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    equipped_hands = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    equipped_feet = models.ForeignKey(
        'items.Equipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    def get_total_weakness(self, style: str) -> float:
        """
        Retorna o multiplicador total de fraqueza do personagem contra
        um tipo de ataque (style), somando todos os equipamentos.
        """
        total_multiplier = 0.0

        for slot, extra in SLOT_WEAKNESS_MULTIPLIER.items():
            equip = getattr(self, slot)

            if not equip:
                continue

            weakness = equip.parsed_stats.defense.weakness

            if weakness == style:
                total_multiplier += extra

        return total_multiplier

    def total_attributes(self):
        """
        Retorna dicionário com atributos base + somatório dos equipamentos
        """
        attrs = {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "arcane": self.arcane,
            "constitution": self.constitution,
            "courage": self.courage,
            "luck": self.luck,
        }

        # Somar todos atributos dos equips
        equipped_items = [
            self.equipped_head, self.equipped_necklace, self.equipped_shoulders,
            self.equipped_chest, self.equipped_hands, self.equipped_feet,
        ]
        for eq in filter(None, equipped_items):
            for attr, val in (eq.attribute_bonuses or {}).items():
                attrs[attr] = attrs.get(attr, 0) + val

        return attrs
    
    @property
    def final_attr(self):
        return self.total_attributes()

    def __str__(self):
        return f"{self.name} (lvl {self.level})"

    def is_idle(self):
        return self.training_start is None and self.resting_start is None

    def add_experience(self, amount, growth_rate=None):
        """
        Adiciona XP e aplica lógica de subir de nível.
        growth_rate = fator de crescimento (ex: 1.5 = 50% mais difícil a cada nível)
        """
        if growth_rate is None:
            growth_rate = (
                CharactersConfig.objects.first().level_growth_rate
            )  # configurável no BD

        self.exp += amount

        leveled_up = False
        # loop para tratar casos em que ganha XP suficiente para subir vários níveis
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            self.attribute_points += 1
            # recalcula xp para próximo nível
            self.max_exp = int(self.max_exp * growth_rate)
            leveled_up = True

        self.save()
        return leveled_up
    
    # --- ATRIBUTOS SECUNDÁRIOS ---
    @property
    def physical_damage(self):
        final = self.final_attr
        return final["strength"] + final["courage"] * 0.1

    @property
    def magical_damage(self):
        final = self.final_attr
        return final["arcane"] + final["courage"] * 0.1

    @property
    def accuracy(self):
        final = self.final_attr
        return final["dexterity"] + final["courage"] * 0.1

    @property
    def crit_chance(self):
        final = self.final_attr
        return min(final["luck"] * 0.5, 50)

    @property
    def crit_damage(self):
        final = self.final_attr
        value = 1 + final["dexterity"] * 0.1 + final["courage"] * 0.01 + final["arcane"] * 0.01
        return round(value, 2)

    @property
    def total_hp(self):
        final = self.final_attr
        return final["constitution"] * 10

    @property
    def total_mana(self):
        final = self.final_attr
        return final["arcane"] * 10
    