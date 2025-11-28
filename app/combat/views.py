from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponseBadRequest
import logging
from .battle import (
    compute_hit_chance, compute_damage, apply_effects_from_passives,
    safe_get_equipment_passives, roll_chance, group_battle_log_by_turns
)
from items.models import EquipmentSlot
from combat.utils import create_mock_equipment

logger = logging.getLogger(__name__)

# imports relativos aos seus apps
from character.models import Character  # ajuste caso o app seja character/tasks/etc
from items.models import Item, Equipment  # itens e equipamentos
from .models import EncounterLog

@login_required
def hunt(request, monster_id=None):
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
        monster.mana = monster.arcane * 10
        monster.max_mana = monster.mana
        monster.emoji = "🤖"
        monster.xp_reward = 10 * monster.level
        monster.gold_reward = 5 * monster.level
        monster.equipment = []
        monster.final_attr = {
            "strength": monster.strength,
            "dexterity": monster.dexterity,
            "arcane": monster.arcane,
            "constitution": monster.constitution,
            "courage": monster.courage,
            "luck": monster.luck,
        }
        slots = [
            EquipmentSlot.HEAD,
            EquipmentSlot.SHOULDERS,
            EquipmentSlot.CHEST,
            EquipmentSlot.FEET,
            EquipmentSlot.HANDS,   # opcional
        ]

        for slot in slots:
            equip = create_mock_equipment(slot)
            setattr(monster, f"equipped_{slot}", equip)

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

    # Inicializar estatísticas
    battle_stats = {
        "total_damage_dealt": 0,
        "total_damage_taken": 0,
        "hits": 0,
        "misses": 0,
        "crits": 0,
        "turns_taken": 0
    }

    char_passives = []
    for slot in ("equipped_head","equipped_necklace","equipped_shoulders","equipped_chest","equipped_hands","equipped_feet"):
        eq = getattr(character, slot, None)
        if eq:
            char_passives += safe_get_equipment_passives(eq)

    mon_passives = []
    for eq in getattr(monster, "equipment", []) or []:
        mon_passives += safe_get_equipment_passives(eq)
    
    char_atk = character.equipped_hands.parsed_stats.attack
    mon_atk_type = "physical"
    char_state["weakness"] = character.get_total_weakness("slash")
    mon_state["weakness"] = 1.1

    MAX_TURNS = 50
    while char_state["hp"] > 0 and mon_state["hp"] > 0 and battle_state["turn"] < MAX_TURNS:
        battle_state["turn"] += 1
        t = battle_state["turn"]
        battle_log.append(f"--- Turno {t} ---")

        # Turn start passives (both sides)
        apply_effects_from_passives(char_passives, "on_turn_start", char_state, mon_state, battle_state, battle_log)
        apply_effects_from_passives(mon_passives, "on_turn_start", mon_state, char_state, battle_state, battle_log)

        # Character attacks first
        hit_chance = compute_hit_chance(character, monster)
        hit_roll = roll_chance(hit_chance)
        if hit_roll:
            damage, crit = compute_damage(char_state, mon_state, damage_type=char_atk.type)
            # apply on_attack passives BEFORE applying damage
            apply_effects_from_passives(char_passives, "on_attack", char_state, mon_state, battle_state, battle_log)
            mon_state["hp"] -= damage
            battle_stats["hits"] += 1
            if crit:
                battle_stats["crits"] += 1
            battle_stats["total_damage_dealt"] += damage
            battle_log.append(f"{character.name} acerta {damage} dano {'(CRÍTICO)' if crit else ''} em {monster.name} (hp restante: {max(0, mon_state['hp'])}).")
            apply_effects_from_passives(mon_passives, "on_receive_damage", mon_state, char_state, battle_state, battle_log)
        else:
            battle_stats["misses"] += 1
            battle_log.append(f"{character.name} errou o ataque em {monster.name}.")

        if mon_state["hp"] <= 0:
            battle_state["winner"] = "character"
            battle_log.append(f"{monster.name} morreu!")
            break

        # Monster attacks
        hit_chance_m = compute_hit_chance(monster, character)
        if roll_chance(hit_chance_m):
            damage_m, crit_m = compute_damage(mon_state, char_state, damage_type=mon_atk_type)
            apply_effects_from_passives(mon_passives, "on_attack", mon_state, char_state, battle_state, battle_log)
            char_state["hp"] -= damage_m
            battle_stats["total_damage_taken"] += damage_m
            battle_log.append(f"{monster.name} acerta {damage_m} dano {'(CRÍTICO)' if crit_m else ''} em {character.name} (hp restante: {max(0, char_state['hp'])}).")
            apply_effects_from_passives(char_passives, "on_receive_damage", char_state, mon_state, battle_state, battle_log)
        else:
            battle_log.append(f"{monster.name} errou o ataque em {character.name}.")

        if char_state["hp"] <= 0:
            battle_state["winner"] = "monster"
            battle_log.append(f"{character.name} foi derrotado!")
            break

    # Atualizar turns_taken
    battle_stats["turns_taken"] = battle_state["turn"]

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
        "battle_stats": battle_stats,
        "char_state": char_state,
        "mon_state": mon_state,
    })