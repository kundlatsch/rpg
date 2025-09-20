from django.db import models
from django.contrib.auth.models import User


class CharactersConfig(models.Model):
    # Progressão de nível
    level_growth_rate = models.FloatField(default=1.5)  # 50% mais difícil a cada nível

class Character(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=5, default="😃")

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
    
    # --- ATRIBUTOS SECUNDÁRIOS (PROPERTIES) ---
    @property
    def physical_damage(self):
        return self.strength + self.courage * 0.1

    @property
    def magical_damage(self):
        return self.arcane + self.courage * 0.1

    @property
    def accuracy(self):
        return self.dexterity + self.courage * 0.1

    @property
    def crit_chance(self):
        # max 50%
        return min(self.luck * 0.5, 50)

    @property
    def crit_damage(self):
        return 1 + self.dexterity * 0.1 + self.courage * 0.01 + self.arcane * 0.01

    @property
    def total_hp(self):
        return self.constitution * 10

    @property
    def total_mana(self):
        return self.arcane * 10