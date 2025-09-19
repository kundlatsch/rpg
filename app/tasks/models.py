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


class Job(models.Model):
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, blank=True, null=True)
    gold_per_minute = models.IntegerField(default=0, blank=True, null=True)
    xp_per_minute = models.IntegerField(default=0, blank=True, null=True)
    drops = models.ManyToManyField(
        "items.Item", blank=True, related_name="jobs_that_drop"
    )
    required_level = models.IntegerField(default=1)
    duration = models.IntegerField(default=5)  # duração fixa do job em minutos

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


class JobRank(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="ranks")
    name = models.CharField(max_length=50)  # nome do rank, não só número
    multiplier = models.FloatField(default=1.0)
    min_xp = models.IntegerField(default=0)  # XP necessário para atingir esse rank

    def __str__(self):
        return f"{self.job.name} - {self.name}"


class CharacterJobProgress(models.Model):
    character = models.ForeignKey("character.Character", on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)

    def current_rank(self):
        # pega o rank correspondente ao XP atual
        ranks = self.job.ranks.order_by("min_xp")
        current = ranks.first()
        for rank in ranks:
            if self.xp >= rank.min_xp:
                current = rank
        return current
