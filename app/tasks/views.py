import logging
import random

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    TasksConfig,
    Job,
    CharacterJob,
    Profession,
    Hunt,
    CharacterHunt,
    HuntMonster
)

from character.models import Character
from items.models import InventoryItem

from datetime import timedelta


logger = logging.getLogger(__name__)


def home(request):
    return render(request, "game/home.html")


@login_required
def create_character(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Character.objects.create(user=request.user, name=name)
        return redirect("dashboard")
    return render(request, "game/create_character.html")


@login_required
def dashboard(request):
    try:
        character = Character.objects.get(user=request.user)
    except Character.DoesNotExist:
        return redirect("create_character")  # redireciona para criar personagem

    # pega XP do treino, se houver, e limpa da sessão
    alert = request.session.pop("alert", None)

    slots = [
        ('Cabeça', '👑', character.equipped_head),
        ('Colar', '📿', character.equipped_necklace),
        ('Ombro', '🎗️', character.equipped_shoulders),
        ('Tronco', '🦺', character.equipped_chest),
        ('Mãos', '🧤', character.equipped_hands),
        ('Pés', '👞', character.equipped_feet),
    ]

    return render(
        request, "game/dashboard.html", {"character": character, "alert": alert, 'equipment_slots': slots}
    )


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # faz login automático após cadastro
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "account/signup.html", {"form": form})


# Treino


@login_required
def training(request):
    """Página que mostra info do treino antes de começar"""
    config = TasksConfig.objects.first()
    character = Character.objects.get(user=request.user)

    # pega o alerta e remove da sessão
    alert = request.session.pop("alert", None)

    time_elapsed = None
    if character.training_start:
        delta = timezone.now() - character.training_start
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        time_elapsed = {"minutes": minutes, "seconds": seconds}

    return render(
        request,
        "game/training.html",
        {
            "config": config,
            "character": character,
            "time_elapsed": time_elapsed,
            "alert": alert,
        },
    )


@login_required
def start_training(request):
    character = Character.objects.get(user=request.user)

    if character.is_idle():
        character.training_start = timezone.now()
        character.save()
    else:
        request.session["alert"] = "Seu personagem já está executando uma atividade!"
        return redirect("dashboard")

    return redirect("training")


@login_required
def end_training(request):
    character = Character.objects.get(user=request.user)
    config = TasksConfig.objects.first()

    if character.training_start:
        # calcula tempo de treino em minutos
        delta = timezone.now() - character.training_start
        minutes = int(delta.total_seconds() // 60)

        # consome stamina proporcional
        stamina_loss = minutes * config.training_stamina_per_minute
        xp_gain = minutes * config.training_xp_per_minute

        character.stamina = max(character.stamina - stamina_loss, 0)
        character.add_experience(xp_gain)
        character.training_start = None
        character.save()

        request.session["alert"] = (
            f"Você treinou por {minutes} minutos e ganhou {xp_gain:.0f} XP!"
        )

    return redirect("training")


# Descanso


@login_required
def resting(request):
    """Página que mostra info do treino antes de começar"""
    config = TasksConfig.objects.first()
    character = Character.objects.get(user=request.user)

    # pega o alerta e remove da sessão
    alert = request.session.pop("alert", None)

    time_elapsed = None
    if character.resting_start:
        delta = timezone.now() - character.resting_start
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        time_elapsed = {"minutes": minutes, "seconds": seconds}

    return render(
        request,
        "game/resting.html",
        {
            "config": config,
            "character": character,
            "time_elapsed": time_elapsed,
            "alert": alert,
        },
    )


@login_required
def start_resting(request):
    character = Character.objects.get(user=request.user)

    if character.is_idle():
        character.resting_start = timezone.now()
        character.save()
    else:
        request.session["alert"] = "Seu personagem já está executando uma atividade!"
        return redirect("dashboard")

    return redirect("resting")


@login_required
def end_resting(request):
    character = Character.objects.get(user=request.user)
    config = TasksConfig.objects.first()

    if character.resting_start:
        # calcula tempo de descanso em minutos
        delta = timezone.now() - character.resting_start
        minutes = int(delta.total_seconds() // 60)

        # recupera atributos proporcional
        hp_gain = minutes * config.rest_hp_per_minute
        mp_gain = minutes * config.rest_mana_per_minute
        st_gain = minutes * config.rest_stamina_per_minute

        character.hp = min(character.hp + hp_gain, character.max_hp)
        character.mana = min(character.mana + mp_gain, character.max_mana)
        character.stamina = min(character.stamina + st_gain, character.max_stamina)
        character.resting_start = None
        character.save()

        request.session["alert"] = f"Você descansou por {minutes} minutos!"

    return redirect("resting")


# Trabalho


@login_required
def jobs_list(request):
    character = get_object_or_404(Character, user=request.user)
    jobs = Job.objects.all()

    jobs_with_prof = []

    for job in jobs:
        try:
            prof, created = Profession.objects.get_or_create(
                character=character,
                profession_type=job.profession_type,
                defaults={"level": 1, "exp": 0, "max_exp": 100}
            )
        except Profession.DoesNotExist:
            prof = None

        jobs_with_prof.append({
            "job": job,
            "prof": prof,
            "is_unlocked": prof and prof.level >= job.required_level,
        })

    return render(
        request,
        "game/jobs.html",
        {
            "character": character,
            "jobs_with_prof": jobs_with_prof,
        },
    )


@login_required
def start_job(request, job_id):
    character = Character.objects.get(user=request.user)
    job = get_object_or_404(Job, id=job_id)

    # Verificar se o personagem tem a profissão necessária
    try:
        profession = Profession.objects.get(
            character=character,
            profession_type=job.profession_type
        )
    except Profession.DoesNotExist:
        request.session["alert"] = "Você não possui a profissão necessária!"
        return redirect("jobs_list")

    # Verificar nível da profissão
    if profession.level < job.required_level:
        request.session["alert"] = "Seu nível nessa profissão é insuficiente!"
        return redirect("jobs_list")

    # Checar se já está em um job
    if CharacterJob.objects.filter(character=character).exists():
        request.session["alert"] = "Você já está trabalhando!"
        return redirect("jobs_list")

    CharacterJob.objects.create(character=character, job=job)
    return redirect("job_in_progress")


@login_required
def job_in_progress(request):
    logger.info("Entrando em job_in_progress para user %s", request.user)
    character = Character.objects.get(user=request.user)
    char_job = CharacterJob.objects.filter(character=character).first()
    if not char_job:
        return redirect("jobs_list")  # não está em nenhum job

    # Calcula se o job terminou
    now = timezone.now()
    end_time = char_job.start_time + timedelta(minutes=char_job.job.duration)
    job_finished = now >= end_time

    time_left = char_job.time_left()
    return render(
        request,
        "game/job_in_progress.html",
        {
            "character": character,
            "char_job": char_job,
            "time_left": time_left,
            "job_finished": job_finished,
        },
    )


@login_required
def end_job(request, job_id):
    character = Character.objects.get(user=request.user)
    char_job = CharacterJob.objects.filter(character=character, job_id=job_id).first()

    if not char_job:
        request.session["alert"] = "Você não está nesse trabalho."
        return redirect("jobs_list")

    job = char_job.job

    # Verifica se terminou
    if char_job.time_left() > 0:
        return redirect("job_in_progress")

    # Recupera a profissão vinculada a esse job
    profession = Profession.objects.get(
        character=character,
        profession_type=job.profession_type
    )

    # Recompensas
    gold_earned = job.gold_per_minute * job.duration
    xp_earned = job.xp_per_minute * job.duration

    # Aplica XP na profissão
    leveled = profession.add_experience(xp_earned)

    # Ouro no personagem
    character.gold += gold_earned
    character.save()

    # Drops
    dropped_items = []
    for item in job.drops.all():
        # Se o item tem drop_chance (precisa existir no model)
        if hasattr(item, "drop_chance"):
            chance = item.drop_chance
        else:
            chance = 100  # fallback

        if random.uniform(0, 100) <= chance:
            dropped_items.append(item)
            inv, created = InventoryItem.objects.get_or_create(
                character=character,
                item=item,
                defaults={"quantity": 0},
            )
            inv.quantity += 1
            inv.save()

    char_job.delete()

    drops_text = (
        ", ".join(i.name for i in dropped_items)
        if dropped_items
        else "nenhum item"
    )

    request.session["alert"] = (
        f"Você recebeu {gold_earned} ouro, {xp_earned} XP "
        f"e encontrou {drops_text}."
    )

    return redirect("jobs_list")

@login_required
def hunts_list(request):
    character = get_object_or_404(Character, user=request.user)
    hunts = Hunt.objects.all()

    return render(request, "game/hunts.html", {
        "character": character,
        "hunts": hunts,
    })

@login_required
def hunt_in_progress(request):
    character = Character.objects.get(user=request.user)
    char_hunt = CharacterHunt.objects.filter(character=character).first()
    if not char_hunt:
        return redirect("hunts_list")

    now = timezone.now()
    end_time = char_hunt.start_time + timedelta(minutes=char_hunt.hunt.duration)
    hunt_finished = now >= end_time

    time_left = char_hunt.time_left()
    return render(
        request,
        "game/hunt_in_progress.html",
        {
            "character": character,
            "char_hunt": char_hunt,
            "time_left": time_left,
            "hunt_finished": hunt_finished,
        },
    )

@login_required
def start_hunt(request, hunt_id):
    character = Character.objects.get(user=request.user)
    hunt = get_object_or_404(Hunt, id=hunt_id)

    if CharacterHunt.objects.filter(character=character).exists():
        request.session["alert"] = "Você já está em uma caçada!"
        return redirect("hunts_list")

    hunt_monsters = HuntMonster.objects.filter(hunt=hunt)

    if not hunt_monsters.exists():
        request.session["alert"] = "Essa caçada não possui monstros cadastrados!"
        return redirect("hunts_list")

    pool = []
    for hm in hunt_monsters:
        pool += [hm] * int(hm.chance)

    monster = random.choice(pool)

    CharacterHunt.objects.create(
        character=character,
        hunt=hunt,
        monster=monster
    )

    return redirect("hunt_in_progress")

@login_required
def end_hunt(request, hunt_id):
    character = Character.objects.get(user=request.user)
    char_hunt = CharacterHunt.objects.filter(
        character=character,
        hunt_id=hunt_id
    ).first()

    if not char_hunt:
        request.session["alert"] = "Você não está nessa caçada."
        return redirect("hunts_list")

    if char_hunt.time_left() > 0:
        return redirect("hunt_in_progress")

    hunt = char_hunt.hunt
    hunt_monster = char_hunt.monster

    char_hunt.delete()

    return redirect("combat:hunt", monster_id=hunt_monster.id)
