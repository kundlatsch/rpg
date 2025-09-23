import random
import logging
from copy import deepcopy
from django.utils import timezone

logger = logging.getLogger(__name__)


VALID_TRIGGERS = {"on_turn_start", "on_attack", "on_defend", "on_hit", "on_receive_damage"}

def safe_get_equipment_passives(equipment):
    """
    Retorna uma lista com todas as PassiveSkill ligadas a um Equipment.
    Se não houver nenhuma, retorna lista vazia.
    """
    if not equipment:
        return []

    # usa o related_name correto definido no model PassiveSkill
    try:
        return list(equipment.passive_skills.all())
    except Exception:
        return []

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

def compute_damage(attacker, defender, physical=True):
    # choose physical or magical; default physical
    if physical:
        base = getattr(attacker, "physical_damage", 1)
    else:
        base = getattr(attacker, "magical_damage", 1)
    # simple defense formula: subtract a portion of constitution
    defense = getattr(defender, "constitution", 0) * 0.5
    dmg = max(1.0, base - defense * 0.1 + random.uniform(-1.0, 1.0))
    # crit?
    crit = False
    crit_chance = getattr(attacker, "crit_chance", 0)
    if roll_chance(crit_chance):
        crit = True
        dmg = dmg * getattr(attacker, "crit_damage", 1.5)
    return int(max(1, round(dmg))), crit

def apply_effects_from_passives(passives, trigger, source_state, target_state, battle_state, logs):
    """
    Passiva é um objeto (modelo) que precisa expor algo como:
      - name, trigger (string)
      - effects: JSON payloads que descrevem o efeito
    Aqui apenas um esqueleto: se PassiveEffect tiver effect_type 'attribute_mod' com payload, aplicamos temporariamente.
    """
    logger.info(passives)
    for p in passives:
        try:
            trig = getattr(p, "trigger", None) or getattr(p, "trigger_name", None)
            if trig != trigger:
                continue
            # attempt to get effects list
            effects = getattr(p, "effects", None) or getattr(p, "effect_payload", None) or getattr(p, "payload", None)
            if not effects:
                # maybe there's a PassiveEffect model related
                related = getattr(p, "passiveeffect_set", None)
                if related is not None:
                    effects = [e.payload if hasattr(e, "payload") else None for e in related.all()]
            if not effects:
                continue

            for eff in effects.all():
                passive_name = eff.passive_skill.name
                if not eff:
                    continue

                # Pega informações do objeto
                etype = eff.effect_type
                payload = eff.payload or {}  # seu JSONField já retorna dict
                target = payload.get("target", eff.target) or "self"

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
                    # exemplo de outro tipo de efeito
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