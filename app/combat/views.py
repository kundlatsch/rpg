from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponseBadRequest
import logging
from .utils import (
    compute_hit_chance, compute_damage, apply_effects_from_passives,
    safe_get_equipment_passives, roll_chance
)

logger = logging.getLogger(__name__)

# imports relativos aos seus apps
from character.models import Character  # ajuste caso o app seja character/tasks/etc
from items.models import Item, Equipment  # itens e equipamentos
from .models import EncounterLog

@login_required
def hunt(request, monster_id=None):
    print("BOCA")
    try:
        character = request.user.character
    except Exception:
        return HttpResponseBadRequest("Usuário não tem personagem.")

    # MOCK MONSTER MODEL
    class SimpleMonster:
        pass

    if monster_id:
        # TODO: usar monstro real
        monster = SimpleMonster()
        monster.name = f"Monstro {monster_id}"
        monster.level = character.level  # balanceamento simples
        monster.strength = max(1, character.strength - 1)
        monster.dexterity = max(1, character.dexterity - 1)
        monster.arcane = max(1, character.arcane - 1)
        monster.constitution = max(1, character.constitution - 1)
        monster.courage = max(1, character.courage - 1)
        monster.luck = max(1, character.luck - 1)
        monster.hp = monster.constitution * 10
        monster.max_hp = monster.hp
        monster.emoji = "👹"
        monster.xp_reward = 20 * monster.level
        monster.gold_reward = 10 * monster.level
        monster.equipment = []
    else:
        monster = SimpleMonster()
        monster.name = "Goblin"
        monster.level = max(1, character.level)
        monster.strength = max(1, character.strength - 1)
        monster.dexterity = max(1, character.dexterity - 1)
        monster.arcane = 1
        monster.constitution = max(1, character.constitution - 1)
        monster.courage = 1
        monster.luck = 1
        monster.hp = monster.constitution * 10
        monster.max_hp = monster.hp
        monster.emoji = "🐾"
        monster.xp_reward = 10 * monster.level
        monster.gold_reward = 5 * monster.level
        monster.equipment = []

    battle_log = []
    battle_state = {
        "start_time": timezone.now(),
        "turn": 0,
        "winner": None,
    }

    char_state = {
        "obj": character,
        "hp": character.hp,
        "_temp_attrs": {},  # atributos temporários aplicados por passivas
    }
    mon_state = {
        "obj": monster,
        "hp": monster.hp,
        "_temp_attrs": {},
    }

    MAX_TURNS = 50
    while char_state["hp"] > 0 and mon_state["hp"] > 0 and battle_state["turn"] < MAX_TURNS:
        battle_state["turn"] += 1
        t = battle_state["turn"]
        battle_log.append(f"--- Turno {t} ---")

        # Turn start passives (both sides)
        # coletar passivas do equipamento do character
        char_passives = []
        for slot in ("equipped_head","equipped_necklace","equipped_shoulders","equipped_chest","equipped_hands","equipped_feet"):
            eq = getattr(character, slot, None)
            if eq:
                char_passives += safe_get_equipment_passives(eq)
        print(char_passives)

        mon_passives = []
        for eq in getattr(monster, "equipment", []) or []:
            mon_passives += safe_get_equipment_passives(eq)

        apply_effects_from_passives(char_passives, "on_turn_start", char_state, mon_state, battle_state, battle_log)
        apply_effects_from_passives(mon_passives, "on_turn_start", mon_state, char_state, battle_state, battle_log)

        # Character attacks first
        hit_chance = compute_hit_chance(character, monster)
        hit_roll = roll_chance(hit_chance)
        if hit_roll:
            damage, crit = compute_damage(character, monster, physical=True)
            # apply on_attack passives BEFORE applying damage
            apply_effects_from_passives(char_passives, "on_attack", char_state, mon_state, battle_state, battle_log)
            mon_state["hp"] -= damage
            battle_log.append(f"{character.name} acerta {damage} dano {'(CRÍTICO)' if crit else ''} em {monster.name} (hp restante: {max(0, mon_state['hp'])}).")
            apply_effects_from_passives(mon_passives, "on_receive_damage", mon_state, char_state, battle_state, battle_log)
        else:
            battle_log.append(f"{character.name} errou o ataque em {monster.name}.")

        if mon_state["hp"] <= 0:
            battle_state["winner"] = "character"
            battle_log.append(f"{monster.name} morreu!")
            break

        # Monster attacks
        # monster's hit chance using same function; wrap monster as object with needed props
        hit_chance_m = compute_hit_chance(monster, character)
        if roll_chance(hit_chance_m):
            damage_m, crit_m = compute_damage(monster, character, physical=True)
            apply_effects_from_passives(mon_passives, "on_attack", mon_state, char_state, battle_state, battle_log)
            char_state["hp"] -= damage_m
            battle_log.append(f"{monster.name} acerta {damage_m} dano {'(CRÍTICO)' if crit_m else ''} em {character.name} (hp restante: {max(0, char_state['hp'])}).")
            apply_effects_from_passives(char_passives, "on_receive_damage", char_state, mon_state, battle_state, battle_log)
        else:
            battle_log.append(f"{monster.name} errou o ataque em {character.name}.")

        if char_state["hp"] <= 0:
            battle_state["winner"] = "monster"
            battle_log.append(f"{character.name} foi derrotado!")
            break

    # Resultado
    if battle_state["winner"] == "character":
        # award xp/gold and optional drops (synchronous)
        xp = getattr(monster, "xp_reward", 0)
        gold = getattr(monster, "gold_reward", 0)

        with transaction.atomic():
            character.hp = max(0, int(char_state["hp"]))
            try:
                leveled = character.add_experience(xp)
            except Exception:
                character.exp += xp
                character.save()
                leveled = False
            # TODO: gold field
            battle_log.append(f"Você ganhou {xp} XP e {gold} ouro.")
        winner = request.user.username
    elif battle_state["winner"] == "monster":
        character.hp = max(0, int(char_state["hp"]))
        character.save()
        winner = "monster"
    else:
        # draw or max turns
        character.hp = max(0, int(char_state["hp"]))
        character.save()
        battle_log.append("Combate terminou por limite de turnos.")
        winner = "draw"

    EncounterLog.objects.create(summary="\n".join(battle_log), winner=winner)

    return render(request, "combat/hunt.html", {
        "battle_log": battle_log,
        "winner": winner,
        "monster": monster,
        "character": character,
    })