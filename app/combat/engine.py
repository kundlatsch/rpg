# combat/engine.py
from django.utils import timezone
from items.models import EquipmentSlot
from .battle import (
    compute_hit_chance, compute_damage, apply_effects_from_passives,
    safe_get_equipment_passives, roll_chance, group_battle_log_by_turns
)

MAX_TURNS = 50


def build_passives_from_equipment(owner):
    passives = []
    for slot in (
        "equipped_head", "equipped_necklace", "equipped_shoulders",
        "equipped_chest", "equipped_hands", "equipped_feet"
    ):
        eq = getattr(owner, slot, None)
        if eq:
            passives += safe_get_equipment_passives(eq)
    return passives


def initialize_state(entity):
    return {
        "obj": entity,
        "hp": entity.hp,
        "_temp_attrs": {},
        "weakness": getattr(entity, "weakness", 1.0),
    }


def run_turn(
    t, char_state, mon_state, char_passives, mon_passives,
    char_atk, monster_atk_type, battle_log, battle_stats, battle_state
):
    battle_log.append(f"--- Turno {t} ---")

    # PASSIVES ON TURN START
    apply_effects_from_passives(char_passives, "on_turn_start",
                                char_state, mon_state, battle_state, battle_log)
    apply_effects_from_passives(mon_passives, "on_turn_start",
                                mon_state, char_state, battle_state, battle_log)

    character = char_state["obj"]
    monster = mon_state["obj"]

    # CHARACTER ATTACKS
    hit_chance = compute_hit_chance(character, monster)
    if roll_chance(hit_chance):
        damage, crit = compute_damage(char_state, mon_state, char_atk.type)
        apply_effects_from_passives(char_passives, "on_attack",
                                    char_state, mon_state, battle_state, battle_log)

        mon_state["hp"] -= damage
        battle_stats["hits"] += 1
        if crit:
            battle_stats["crits"] += 1
        battle_stats["total_damage_dealt"] += damage

        battle_log.append(
            f"{character.name} acerta {damage} dano "
            f"{'(CRÍTICO)' if crit else ''} em {monster.name} "
            f"(hp restante: {max(0, mon_state['hp'])})."
        )

        apply_effects_from_passives(mon_passives, "on_receive_damage",
                                    mon_state, char_state, battle_state, battle_log)
    else:
        battle_stats["misses"] += 1
        battle_log.append(f"{character.name} errou o ataque em {monster.name}.")

    if mon_state["hp"] <= 0:
        battle_state["winner"] = "character"
        battle_log.append(f"{monster.name} morreu!")
        return

    # MONSTER ATTACKS
    hit_chance_m = compute_hit_chance(monster, character)
    if roll_chance(hit_chance_m):
        damage_m, crit_m = compute_damage(mon_state, char_state, monster_atk_type)
        apply_effects_from_passives(mon_passives, "on_attack",
                                    mon_state, char_state, battle_state, battle_log)

        char_state["hp"] -= damage_m
        battle_stats["total_damage_taken"] += damage_m

        battle_log.append(
            f"{monster.name} acerta {damage_m} dano "
            f"{'(CRÍTICO)' if crit_m else ''} em {character.name} "
            f"(hp restante: {max(0, char_state['hp'])})."
        )

        apply_effects_from_passives(char_passives, "on_receive_damage",
                                    char_state, mon_state, battle_state, battle_log)
    else:
        battle_log.append(f"{monster.name} errou o ataque em {character.name}.")

    if char_state["hp"] <= 0:
        battle_state["winner"] = "monster"
        battle_log.append(f"{character.name} foi derrotado!")
        return


def finalize_battle(character, monster, battle_log, battle_state, char_state):
    winner = battle_state["winner"]
    character.hp = max(0, int(char_state["hp"]))
    character.save()
    if winner == "character":
        return "character"

    elif winner == "monster":
        return "monster"

    else:
        battle_log.append("Combate terminou por limite de turnos.")
        return "draw"


def run_battle(character, monster):
    """Executa TODO o combate e retorna um dicionário com tudo que a view precisa."""
    battle_log = []
    battle_state = {
        "start_time": timezone.now(),
        "turn": 0,
        "winner": None,
    }

    char_state = initialize_state(character)
    mon_state = initialize_state(monster)

    battle_stats = {
        "total_damage_dealt": 0,
        "total_damage_taken": 0,
        "hits": 0,
        "misses": 0,
        "crits": 0,
        "turns_taken": 0
    }

    char_passives = build_passives_from_equipment(character)
    mon_passives = []  # seus monstros mock não têm passivas por enquanto

    char_atk = character.equipped_hands.parsed_stats.attack
    monster_atk_type = "physical"

    for t in range(1, MAX_TURNS + 1):
        battle_state["turn"] = t
        run_turn(
            t, char_state, mon_state, char_passives, mon_passives,
            char_atk, monster_atk_type,
            battle_log, battle_stats, battle_state
        )

        if battle_state["winner"] is not None:
            break

    battle_stats["turns_taken"] = battle_state["turn"]
    final_winner = finalize_battle(character, monster, battle_log, battle_state, char_state)

    return {
        "battle_log": battle_log,
        "winner": final_winner,
        "monster": monster,
        "character": character,
        "battle_stats": battle_stats,
        "char_state": char_state,
        "mon_state": mon_state,
    }
