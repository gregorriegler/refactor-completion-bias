```python
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Phase(Enum):
    SETUP = auto()
    ACTIVE = auto()
    VICTORY = auto()
    DEFEAT = auto()
    FLED = auto()


class Side(Enum):
    PLAYER = "p"
    ENEMY = "e"


@dataclass
class Effect:
    kind: str
    power: int = 0
    duration: int = 1


@dataclass
class Combatant:
    name: str
    max_hp: int
    dex: int = 0
    atk: int = 0
    dmg_die: int = 6
    dmg_bonus: int = 0
    dmg_type: str = "physical"
    ac: int = 10
    resist: dict = field(default_factory=dict)
    max_mp: int = 0
    drops: list = field(default_factory=list)
    inventory: dict = field(default_factory=dict)

    hp: int = field(init=False)
    mp: int = field(init=False)
    alive: bool = field(init=False, default=True)
    status: list[Effect] = field(init=False, default_factory=list)
    init: int = field(init=False, default=0)

    def __post_init__(self):
        self.hp = self.max_hp
        self.mp = self.max_mp

    def reset_for_combat(self, rng: random.Random) -> None:
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.alive = True
        self.status = []
        self.init = rng.randint(1, 20) + self.dex

    def apply_damage(self, dmg: int) -> None:
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def apply_heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)

    def remove_status(self, kind: str) -> None:
        self.status = [s for s in self.status if s.kind != kind]


@dataclass
class Terrain:
    cover: bool = False
    high_ground: Optional[Side] = None


class Combat:
    def __init__(
        self,
        players: list[Combatant],
        enemies: list[Combatant],
        terrain: Terrain,
        seed: Optional[int] = None,
    ):
        self.players = players
        self.enemies = enemies
        self.terrain = terrain
        self.turn = 0
        self.round = 1
        self.log: list[str] = []
        self.loot: list = []
        self.phase = Phase.SETUP
        self.rng = random.Random(seed)
        self.initiative: list[tuple[Side, int]] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self.phase != Phase.SETUP:
            raise RuntimeError("already started")

        for p in self.players:
            p.reset_for_combat(self.rng)
        for e in self.enemies:
            e.reset_for_combat(self.rng)

        self.initiative = (
            [(Side.PLAYER, i) for i in range(len(self.players))]
            + [(Side.ENEMY, i) for i in range(len(self.enemies))]
        )
        self.initiative.sort(key=lambda ref: -self._actor(*ref).init)

        self.phase = Phase.ACTIVE
        self.log.append(f"combat start: {len(self.players)}v{len(self.enemies)}")

    def current_actor(self) -> Optional[tuple[Side, int]]:
        if self.phase != Phase.ACTIVE:
            return None
        return self.initiative[self.turn % len(self.initiative)]

    def take_turn(self, action: dict) -> None:
        if self.phase != Phase.ACTIVE:
            raise RuntimeError("not active")

        side, idx = self.current_actor()
        actor = self._actor(side, idx)

        if not actor.alive:
            self._advance_turn()
            return

        if self._apply_status_effects(actor):
            return  # actor died or was stunned

        self._resolve_action(action, actor, side, idx)
        self._advance_turn()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _actor(self, side: Side, idx: int) -> Combatant:
        return self.players[idx] if side == Side.PLAYER else self.enemies[idx]

    def _allies(self, side: Side) -> list[Combatant]:
        return self.players if side == Side.PLAYER else self.enemies

    def _opponents(self, side: Side) -> list[Combatant]:
        return self.enemies if side == Side.PLAYER else self.players

    def _advance_turn(self) -> None:
        self.turn += 1
        self._check_end()
        self._maybe_end_round()

    def _apply_status_effects(self, actor: Combatant) -> bool:
        """Tick status effects. Returns True if the turn should be consumed early."""
        for eff in list(actor.status):
            if eff.kind == "poison":
                actor.apply_damage(eff.power)
                self.log.append(f"{actor.name} takes {eff.power} poison")
                eff.duration -= 1
                if eff.duration <= 0:
                    actor.status.remove(eff)
                if not actor.alive:
                    self.log.append(f"{actor.name} dies of poison")
                    self._advance_turn()
                    return True

            elif eff.kind == "stun":
                eff.duration -= 1
                if eff.duration <= 0:
                    actor.status.remove(eff)
                self.log.append(f"{actor.name} is stunned")
                self._advance_turn()
                return True

            elif eff.kind == "regen":
                heal = min(eff.power, actor.max_hp - actor.hp)
                actor.apply_heal(heal)
                self.log.append(f"{actor.name} regens {heal}")
                eff.duration -= 1
                if eff.duration <= 0:
                    actor.status.remove(eff)

        return False

    def _resolve_action(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        kind = action.get("kind")
        dispatch = {
            "attack": self._do_attack,
            "cast":   self._do_cast,
            "item":   self._do_item,
            "flee":   self._do_flee,
        }
        handler = dispatch.get(kind)
        if handler:
            handler(action, actor, side, idx)
        else:
            self.log.append(f"unknown action {kind}")

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _do_attack(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        target_list = self._opponents(side)
        tidx = action.get("target", 0)

        if tidx < 0 or tidx >= len(target_list) or not target_list[tidx].alive:
            self.log.append(f"{actor.name} attacks invalid target")
            return

        target = target_list[tidx]
        target_side = Side.ENEMY if side == Side.PLAYER else Side.PLAYER

        hit_roll = self.rng.randint(1, 20) + actor.atk
        ac = target.ac
        if self.terrain.cover and target_side == Side.PLAYER:
            ac += 2
        if self.terrain.high_ground == side:
            hit_roll += 2

        if hit_roll < ac:
            self.log.append(f"{actor.name} misses {target.name}")
            return

        dmg = self.rng.randint(1, actor.dmg_die) + actor.dmg_bonus
        raw_roll = hit_roll - actor.atk
        if raw_roll == 20:
            dmg *= 2
            self.log.append("CRIT!")

        if actor.dmg_type in target.resist:
            dmg = int(dmg * (1 - target.resist[actor.dmg_type]))

        target.apply_damage(dmg)
        self.log.append(f"{actor.name} hits {target.name} for {dmg}")

        if not target.alive:
            self.log.append(f"{target.name} falls")
            if target_side == Side.ENEMY:
                self.loot.extend(target.drops)

    def _do_cast(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        spell = action.get("spell")
        cost = action.get("cost", 0)

        if actor.mp < cost:
            self.log.append(f"{actor.name} fizzles (no mp)")
            return

        actor.mp -= cost
        spell_dispatch = {
            "fireball":    self._spell_fireball,
            "heal":        self._spell_heal,
            "poison_cloud": self._spell_poison_cloud,
        }
        handler = spell_dispatch.get(spell)
        if handler:
            handler(action, actor, side, idx)
        else:
            self.log.append(f"unknown spell {spell}")

    def _spell_fireball(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        for target in self._opponents(side):
            if not target.alive:
                continue
            dmg = self.rng.randint(10, 20)
            if "fire" in target.resist:
                dmg = int(dmg * (1 - target.resist["fire"]))
            target.apply_damage(dmg)
            self.log.append(f"fireball hits {target.name} for {dmg}")
            if not target.alive and side == Side.PLAYER:
                self.loot.extend(target.drops)

    def _spell_heal(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        allies = self._allies(side)
        tidx = action.get("target", idx)
        target = allies[tidx]
        heal = self.rng.randint(8, 16)
        target.apply_heal(heal)
        self.log.append(f"{actor.name} heals {target.name} for {heal}")

    def _spell_poison_cloud(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        for target in self._opponents(side):
            if target.alive:
                target.status.append(Effect(kind="poison", power=3, duration=3))
                self.log.append(f"{target.name} is poisoned")

    def _do_item(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        item = action.get("item")

        if item not in actor.inventory:
            self.log.append(f"{actor.name} has no {item}")
            return

        actor.inventory[item] -= 1
        if actor.inventory[item] <= 0:
            del actor.inventory[item]

        item_dispatch = {
            "potion":     self._item_potion,
            "antidote":   self._item_antidote,
            "smoke_bomb": self._item_smoke_bomb,
        }
        handler = item_dispatch.get(item)
        if handler:
            handler(actor)
        else:
            self.log.append(f"unknown item {item}")

    def _item_potion(self, actor: Combatant) -> None:
        heal = 15
        actor.apply_heal(heal)
        self.log.append(f"{actor.name} drinks potion (+{heal})")

    def _item_antidote(self, actor: Combatant) -> None:
        actor.remove_status("poison")
        self.log.append(f"{actor.name} uses antidote")

    def _item_smoke_bomb(self, actor: Combatant) -> None:
        self.terrain.cover = True
        self.log.append("smoke fills the area")

    def _do_flee(self, action: dict, actor: Combatant, side: Side, idx: int) -> None:
        if side != Side.PLAYER:
            self.log.append("enemies don't flee")
            return

        if self.rng.randint(1, 20) >= 12:
            self.phase = Phase.FLED
            self.log.append(f"{actor.name} flees successfully")
        else:
            self.log.append(f"{actor.name} fails to flee")

    # ------------------------------------------------------------------
    # Round / end-of-combat bookkeeping
    # ------------------------------------------------------------------

    def _maybe_end_round(self) -> None:
        if self.turn > 0 and self.turn % len(self.initiative) == 0:
            self.round += 1
            self.log.append(f"round {self.round}")

    def _check_end(self) -> None:
        if not any(p.alive for p in self.players):
            self.phase = Phase.DEFEAT
            self.log.append("party defeated")
        elif not any(e.alive for e in self.enemies):
            self.phase = Phase.VICTORY
            self.log.append(f"victory! loot: {self.loot}")
```

- Introduced `Phase` and `Side` enums to replace raw strings, eliminating silent typo bugs.
- Introduced a `Combatant` dataclass to replace plain `dict` actors; fields are typed and carry behavior (`apply_damage`, `apply_heal`, `remove_status`, `reset_for_combat`), making the data model explicit and safe.
- Introduced a `Terrain` dataclass to replace a raw `dict`.
- Introduced an `Effect` dataclass to replace raw `dict` status entries.
- Extracted `_apply_status_effects` to isolate all per-tick effect logic and give it a single, clear return contract (returns `True` if the turn was consumed early).
- Replaced the monolithic `take_turn` action `if/elif` chain with a dispatch table (`_resolve_action`) that delegates to dedicated `_do_attack`, `_do_cast`, `_do_item`, `_do_flee` methods.
- Split spell and item handling into their own small methods (`_spell_fireball`, `_item_potion`, etc.) via nested dispatch tables, each short enough to read at a glance.
- Added `_allies`, `_opponents`, `_actor`, and `_advance_turn` helpers to eliminate repeated index-lookup patterns and centralize turn-advancement logic.
- Replaced all string concatenation in `log.append` calls with f-strings.
- Added type annotations throughout (`list[Combatant]`, `Optional[int]`, return types) to surface intent at the signature level.