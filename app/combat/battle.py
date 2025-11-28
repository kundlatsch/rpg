import random
import logging
from copy import deepcopy
from django.utils import timezone

logger = logging.getLogger(__name__)


VALID_TRIGGERS = {"on_turn_start", "on_attack", "on_defend", "on_hit", "on_receive_damage"}

def compute_final_attrs(state):
    """
    Retorna os atributos PRIMÁRIOS após aplicar buffs/debuffs temporários.
    Esses atributos serão usados pelas propriedades secundárias do Character.
    """
    obj = state["obj"]
    final = obj.final_attr.copy()

    for attr, delta in state.get("_temp_attrs", {}).items():
        final[attr] = final.get(attr, 0) + delta

    return final

def compute_secondary_stats(final_attrs):
    """
    Computa atributos secundários a partir de atributos primários já modificados.
    """
    strength = final_attrs.get("strength", 1)
    dexterity = final_attrs.get("dexterity", 1)
    arcane = final_attrs.get("arcane", 1)
    constitution = final_attrs.get("constitution", 1)
    courage = final_attrs.get("courage", 1)
    luck = final_attrs.get("luck", 1)

    return {
        "physical_damage": strength + courage * 0.1,
        "magical_damage": arcane + courage * 0.1,
        "accuracy": dexterity + courage * 0.1,
        "crit_chance": min(luck * 0.5, 50),  # % máx 50%
        "crit_damage": 1 + dexterity * 0.1 + courage * 0.01 + arcane * 0.01,
        "total_hp": constitution * 10,
        "total_mana": arcane * 10,
        "defense": constitution,
    }


def safe_get_equipment_passives(equipment):
    """
    Retorna uma lista com todas as PassiveSkill ligadas a um Equipment.
    Se não houver nenhuma, retorna lista vazia.
    """
    if not equipment:
        return []

    passive = equipment.passive_skill or {}

    # Se o JSON estiver vazio, considere como sem passiva
    if not passive or not isinstance(passive, dict):
        return []

    return [passive]

def roll_chance(percent):
    return random.random() * 100.0 < float(percent)

def compute_hit_chance(attacker, defender):
    # 65% + (attacker.accuracy - defender.dexterity) * 2 (tweakable)
    base = 65.0
    diff = (getattr(attacker, "accuracy", 0) - getattr(defender, "dexterity", 0))
    hit = base + diff * 2.0
    # clamp
    hit = max(5.0, min(95.0, hit))
    return hit

def compute_damage(attacker_state, defender_state, damage_type="physical"):
    logger.info("===== COMPUTE DAMAGE =====")
    logger.info(f"Damage type: {damage_type}")

    # --------------------------------------------------------
    #   1. Atributos finais (primários)
    # --------------------------------------------------------
    atk_primary = compute_final_attrs(attacker_state)
    def_primary = compute_final_attrs(defender_state)

    logger.debug(f"Attacker PRIMARY: {atk_primary}")
    logger.debug(f"Defender PRIMARY: {def_primary}")

    # --------------------------------------------------------
    #   2. Atributos secundários
    # --------------------------------------------------------
    atk_sec = compute_secondary_stats(atk_primary)
    def_sec = compute_secondary_stats(def_primary)

    logger.debug(f"Attacker SECONDARY: {atk_sec}")
    logger.debug(f"Defender SECONDARY: {def_sec}")

    # --------------------------------------------------------
    #   3. Base damage
    # --------------------------------------------------------
    if damage_type == "physical":
        base_dmg = atk_sec["physical_damage"]
    else:
        base_dmg = atk_sec["magical_damage"]

    logger.info(f"Base damage from stats ({damage_type}): {base_dmg}")

    # --------------------------------------------------------
    #   4. Weapon damage
    # --------------------------------------------------------
    weapon_damage = 0
    attacker = attacker_state.get("obj")

    if attacker:
        try:
            weapon_damage = attacker.equipped_hands.parsed_stats.attack.value or 0
            base_dmg += weapon_damage
            logger.info(f"Weapon damage: {weapon_damage}")
        except Exception as e:
            logger.warning(f"No weapon damage found: {e}")

    logger.info(f"Base damage after weapon: {base_dmg}")

    # --------------------------------------------------------
    #   5. Defense
    # --------------------------------------------------------
    defender = defender_state.get("obj")
    defense_value = def_sec["defense"]

    logger.info(f"Initial defense (secondary stat): {defense_value}")

    if defender:
        slots = [
            "equipped_head",
            "equipped_necklace",
            "equipped_shoulders",
            "equipped_chest",
            "equipped_feet",
        ]

        for slot in slots:
            equip = getattr(defender, slot, None)
            if not equip:
                logger.debug(f"No equip in slot {slot}")
                continue
            logger.debug(f">>> {equip.parsed_stats.defense.value}")
            armor_value = getattr(equip.parsed_stats.defense, "value", None)

            logger.debug(
                f"Slot {slot}: armor_value={armor_value} ({equip.item.name if equip else 'none'})"
            )

            if isinstance(armor_value, int):
                defense_value += armor_value

    logger.info(f"Total raw defense before 0.5 multiplier: {defense_value}")

    defense_value *= 0.5
    logger.info(f"Defense after multiplier: {defense_value}")

    dmg = base_dmg - defense_value
    logger.info(f"Damage after subtracting defense: {dmg}")

    # Variação aleatória
    random_variation = random.uniform(-1.0, 1.0)
    dmg = max(1.0, dmg + random_variation)

    logger.info(f"Damage after random variation ({random_variation}): {dmg}")

    # --------------------------------------------------------
    #   6. Critical hit
    # --------------------------------------------------------
    crit = False
    if random.random() < (atk_sec["crit_chance"] / 100):
        crit = True
        dmg *= atk_sec["crit_damage"]
        logger.info(f"CRITICAL HIT! Crit multiplier: {atk_sec['crit_damage']}")

    # --------------------------------------------------------
    #   7. Weakness
    # --------------------------------------------------------
    weakness = defender_state.get("weakness", 0.0)
    logger.info(f"Weakness multiplier: {weakness}")

    if weakness > 0:
        dmg *= (1 + weakness)
        logger.info(f"Damage after weakness: {dmg}")

    # --------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------
    final_damage = int(max(1, round(dmg)))

    logger.info(f"FINAL DAMAGE = {final_damage}, CRITICAL = {crit}")
    logger.info("===== END DAMAGE CALC =====\n")

    return final_damage, crit



def apply_effects_from_passives(passives, trigger, source_state, target_state, battle_state, logs):
    """
    Passiva é um objeto (modelo) que precisa expor algo como:
      - name, trigger (string)
      - effects: JSON payloads que descrevem o efeito
    Aqui apenas um esqueleto: se PassiveEffect tiver effect_type 'attribute_mod' com payload, aplicamos temporariamente.
    """
    for p in passives:
        try:
            if p.get("trigger") != trigger:
                continue

            effects = p.get("effects", [])
            if not effects:
                continue

            passive_name = p.get("name")
            source_char = source_state.get("obj")
            passive_cost = p.get("cost")

            if source_char and passive_cost and passive_cost > source_char.mana:
                logs.append(f"Passiva {passive_name} não pode ser ativada por falta de mana.")
                continue
            else:
                source_char.mana -= passive_cost
                source_char.save()

            for effect in effects:

                etype = effect.get("type")
                payload = effect.get("payload") or {}
                target = effect.get("target") or "self"

                if etype in ("attribute_mod", "attr_mod"):
                    attr = payload.get("attribute")
                    val = payload.get("value", 0)
                    duration = payload.get("duration", 1)
                    tgt_state = source_state if target == "self" else target_state

                    if attr:
                        # pega valor atual (se já foi modificado) ou do objeto
                        prev = tgt_state["_temp_attrs"].get(attr, getattr(tgt_state["obj"], attr, 0))
                        tgt_state["_temp_attrs"][attr] = prev + val
                        logs.append(
                            f"Passiva {passive_name}: aplicou {val} em {attr} para {target} por {duration} turno(s)."
                        )

                elif etype == "status_effect":
                    status_name = payload.get("status")
                    duration = payload.get("duration", 1)
                    logs.append(f"Passiva {passive_name}: aplicou status {status_name} em {target} por {duration} turno(s).")

                elif etype == "deal_damage":
                    dmg = payload.get("damage", 0)
                    tgt_state = source_state if target == "self" else target_state
                    tgt_state["obj"].hp -= dmg
                    logs.append(f"Passiva {passive_name}: causou {dmg} de dano em {target}.")
                # TODO: implement other effects.
        except Exception as e:
            logger.exception("Erro aplicando passiva %s: %s", p, e)
            continue

def group_battle_log_by_turns(battle_log):
    turns = []
    current_turn = None
    current_messages = []
    for line in battle_log:
        if line.startswith("--- Turno "):
            if current_turn is not None:
                turns.append({"turn": current_turn, "messages": current_messages})
            current_turn = int(line.split(" ")[2])
            current_messages = []
        else:
            current_messages.append(line)
    if current_turn is not None:
        turns.append({"turn": current_turn, "messages": current_messages})
    return turns

