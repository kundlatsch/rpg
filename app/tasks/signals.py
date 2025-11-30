from django.db.models.signals import post_save
from django.dispatch import receiver
from character.models import Character
from tasks.models import Profession, ProfessionType

@receiver(post_save, sender=Character)
def create_professions_for_character(sender, instance, created, **kwargs):
    if not created:
        return

    # cria uma Profession para cada ProfessionType existente
    for ptype in ProfessionType.objects.all():
        Profession.objects.create(
            character=instance,
            profession_type=ptype,
        )
