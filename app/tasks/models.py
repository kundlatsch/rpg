from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class TasksConfig(models.Model):
    # Configurações de treino
    training_stamina_per_minute = models.IntegerField(default=5)
    training_xp_per_minute = models.IntegerField(default=10)

    # Configurações de descanso
    rest_stamina_per_minute = models.IntegerField(default=5)
    rest_hp_per_minute = models.IntegerField(default=5)
    rest_mana_per_minute = models.IntegerField(default=5)

    def __str__(self):
        return (
            f"Treino {self.training_stamina_per_minute}/{self.training_xp_per_minute} "
            f"Descanso {self.rest_stamina_per_minute}/{self.rest_hp_per_minute}/{self.rest_mana_per_minute}"
        )

class ProfessionType(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, default="")
    emoji = models.CharField(max_length=10, blank=True)
    level_growth_rate = models.FloatField(default=1.5)

class Profession(models.Model):
    character = models.ForeignKey("character.Character", on_delete=models.CASCADE)
    profession_type = models.ForeignKey(
        "tasks.ProfessionType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    max_exp = models.IntegerField(default=100)

    def add_experience(self, amount):
        """
        Adiciona XP e aplica lógica de subir de nível.
        growth_rate = fator de crescimento (ex: 1.5 = 50% mais difícil a cada nível)
        """
        self.exp += amount

        leveled_up = False
        # loop para tratar casos em que ganha XP suficiente para subir vários níveis
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            # recalcula xp para próximo nível
            self.max_exp = int(self.max_exp * self.profession_type.level_growth_rate)
            leveled_up = True

        self.save()
        return leveled_up

class Job(models.Model):
    profession_type = models.ForeignKey(
        "tasks.ProfessionType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, default="")
    emoji = models.CharField(max_length=10, blank=True, null=True)
    gold_per_minute = models.IntegerField(default=0)
    xp_per_minute = models.IntegerField(default=0)
    drops = models.ManyToManyField("items.Item", blank=True)
    required_level = models.IntegerField(default=1)
    duration = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.emoji or ''} {self.name}"


class CharacterJob(models.Model):
    """Ligação do personagem com o job atual"""

    character = models.OneToOneField("character.Character", on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)

    def time_left(self):
        elapsed = (timezone.now() - self.start_time).total_seconds() // 60
        return max(self.job.duration - int(elapsed), 0)

class Hunt(models.Model):
    """Uma caçada disponível para o jogador escolher."""
    name = models.CharField(max_length=100)
    duration = models.IntegerField(default=5)  # minutos
    required_level = models.IntegerField(default=1)
    description = models.TextField(default="Enfrente criaturas perigosas nesta caçada.")
    difficulty = models.IntegerField(default=1, help_text="Dificuldade de 1 (mais fácil) a 5 (mais difícil).") 

    def __str__(self):
        return self.name


class HuntMonster(models.Model):
    """Monstros possíveis dentro de uma caçada."""
    hunt = models.ForeignKey(Hunt, related_name="monsters", on_delete=models.CASCADE)
    monster = models.ForeignKey(
        "character.Character",
        on_delete=models.CASCADE,
        limit_choices_to={"type": "monster"},
    )
    chance = models.FloatField(default=100)
    xp_drop = models.IntegerField(default=0)
    gold_drop = models.IntegerField(default=0)
    item_drops = models.ManyToManyField("items.Item", blank=True)

    @property
    def item_drops_display(self):
        items = self.item_drops.all()

        if not items:
            return "Nenhum item"

        formatted = []
        for item in items:
            formatted.append(f"{item.emoji} {item.name}")

        return ", ".join(formatted)

    def __str__(self):
        return f"{self.monster.name} ({self.chance}%)"


class CharacterHunt(models.Model):
    """Guarda a caçada em andamento do jogador."""
    character = models.OneToOneField("character.Character", on_delete=models.CASCADE)
    hunt = models.ForeignKey(Hunt, on_delete=models.CASCADE)
    monster = models.ForeignKey(
        HuntMonster,
        on_delete=models.CASCADE,
        related_name="selected_monster"
    )
    start_time = models.DateTimeField(default=timezone.now)

    def time_left(self):
        elapsed = (timezone.now() - self.start_time).total_seconds() // 60
        return max(self.hunt.duration - int(elapsed), 0)
