from django.db import models


class EncounterLog(models.Model):
    """
    Opcional: armazena resumo de encontros (não usado obrigatoriamente pela view).
    Útil para histórico. Pode ser estendido mais tarde.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True)
    winner = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Encounter {self.id} - {self.winner or 'N/A'}"