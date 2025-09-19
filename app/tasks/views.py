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
    JobRank,
    CharacterJobProgress,
    CharacterJob,
)

from character.models import Character

from datetime import timedelta


logger = logging.getLogger(__name__)


def home(request):
    return render(request, "game/home.html")


@login_required
def create_character(request):
    if request.method == "POST":
        name = request.POST.get("name")
        char_class = request.POST.get("char_class")
        Character.objects.create(user=request.user, name=name, char_class=char_class)
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

    return render(
        request, "game/dashboard.html", {"character": character, "alert": alert}
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
    character = Character.objects.get(user=request.user)

    if CharacterJob.objects.filter(character=character).exists():
        return redirect("job_in_progress")

    jobs = Job.objects.all()

    # Pegar progresso de cada job para o personagem
    progress_dict = {}
    for job in jobs:
        progress, created = CharacterJobProgress.objects.get_or_create(
            character=character, job=job
        )
        progress_dict[job.id] = progress

    return render(
        request,
        "game/jobs.html",
        {"character": character, "jobs": jobs, "progress_dict": progress_dict},
    )


@login_required
def start_job(request, job_id):
    character = Character.objects.get(user=request.user)
    job = get_object_or_404(Job, id=job_id)

    # Verificar nível
    if character.level < job.required_level:
        logger.warning(
            "Nível insuficiente: level %s < requerido %s",
            character.level,
            job.required_level,
        )
        request.session["alert"] = "Você não tem nível suficiente para este trabalho!"
        return redirect("jobs_list")

    # Se já estiver em trabalho, não deixa começar outro
    if CharacterJob.objects.filter(character=character).exists():
        logger.warning("Character %s já está em um trabalho", character)
        request.session["alert"] = "Você já está em um trabalho!"
        return redirect("jobs_list")

    CharacterJob.objects.create(character=character, job=job, start_time=timezone.now())
    logger.info("CharacterJob criado com sucesso para %s no job %s", character, job)
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
    elapsed = timezone.now() - char_job.start_time
    elapsed_minutes = elapsed.total_seconds() / 60

    # só libera se já passou o duration do job
    if elapsed_minutes < job.duration:
        minutes_left = int(job.duration - elapsed_minutes)
        messages.warning(
            request, f"Você ainda não concluiu este trabalho! Falta {minutes_left} min."
        )
        return redirect("job_in_progress")

    # recompensa
    gold_earned = job.gold_per_minute * job.duration
    xp_earned = job.xp_per_minute * job.duration

    character.add_experience(xp_earned)
    # se você tiver um campo de ouro no Character:
    # character.gold += gold_earned

    # calcula drops
    dropped_items = []
    for drop in job.drops.all():
        if random.uniform(0, 100) <= drop.item.drop_chance:
            dropped_items.append(drop)
            # aqui você pode salvar no inventário do personagem
            # CharacterInventory.objects.create(character=character, item=drop.item, quantity=1)

    character.save()
    char_job.delete()

    drops_names = (
        ", ".join(str(drop.item.name) for drop in dropped_items)
        if dropped_items
        else "nenhum item"
    )
    request.session["alert"] = (
        f"Você recebeu {gold_earned} ouro, {xp_earned} XP e dropou {drops_names}."
    )
    return redirect("jobs_list")
