from django.db import models
from django.contrib.auth.models import User


class CharactersConfig(models.Model):
    # Progressão de nível
    level_growth_rate = models.FloatField(default=1.5)  # 50% mais difícil a cada nível

class Character(models.Model):
    CLASS_CHOICES = [
        ("mage", "Mago"),
        ("warrior", "Guerreiro"),
        ("archer", "Arqueiro"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    char_class = models.CharField(max_length=20, choices=CLASS_CHOICES)

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

    def __str__(self):
        return f"{self.name} ({self.get_char_class_display()})"

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