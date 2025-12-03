from django.db import models


class EncounterLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True)
    winner = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Encounter {self.id} - {self.winner or 'N/A'}"
    
class ArenaRanking(models.Model):
    character = models.OneToOneField("character.Character", on_delete=models.CASCADE)
    points = models.IntegerField(default=1000)

    def __str__(self):
        return f"{self.character.name} - {self.points} pts"