# Example 15: Turn-based combat simulator (tangled state machine)

```python
import random

class Combat:
    def __init__(self, players, enemies, terrain, seed=None):
        self.players = players
        self.enemies = enemies
        self.terrain = terrain
        self.turn = 0
        self.round = 1
        self.log = []
        self.effects = []
        self.loot = []
        self.phase = "setup"
        self.rng = random.Random(seed)
        self.initiative = []

    def start(self):
        if self.phase != "setup":
            raise RuntimeError("already started")
        for p in self.players:
            p["hp"] = p["max_hp"]
            p["mp"] = p.get("max_mp", 0)
            p["alive"] = True
            p["status"] = []
            p["init"] = self.rng.randint(1, 20) + p.get("dex", 0)
        for e in self.enemies:
            e["hp"] = e["max_hp"]
            e["alive"] = True
            e["status"] = []
            e["init"] = self.rng.randint(1, 20) + e.get("dex", 0)
        self.initiative = [("p", i) for i in range(len(self.players))] + \
                          [("e", i) for i in range(len(self.enemies))]
        def init_key(ref):
            side, idx = ref
            return -(self.players[idx]["init"] if side == "p" else self.enemies[idx]["init"])
        self.initiative.sort(key=init_key)
        self.phase = "active"
        self.log.append("combat start: " + str(len(self.players)) + "v" + str(len(self.enemies)))

    def current_actor(self):
        if self.phase != "active":
            return None
        return self.initiative[self.turn % len(self.initiative)]

    def take_turn(self, action):
        if self.phase != "active":
            raise RuntimeError("not active")
        side, idx = self.current_actor()
        actor = self.players[idx] if side == "p" else self.enemies[idx]
        if not actor["alive"]:
            self.turn += 1
            self._maybe_end_round()
            return
        for eff in list(actor["status"]):
            if eff["kind"] == "poison":
                actor["hp"] -= eff["power"]
                self.log.append(actor["name"] + " takes " + str(eff["power"]) + " poison")
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
                if actor["hp"] <= 0:
                    actor["alive"] = False
                    self.log.append(actor["name"] + " dies of poison")
                    self.turn += 1
                    self._check_end()
                    return
            elif eff["kind"] == "stun":
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
                self.log.append(actor["name"] + " is stunned")
                self.turn += 1
                self._maybe_end_round()
                return
            elif eff["kind"] == "regen":
                heal = min(eff["power"], actor["max_hp"] - actor["hp"])
                actor["hp"] += heal
                self.log.append(actor["name"] + " regens " + str(heal))
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
        kind = action.get("kind")
        if kind == "attack":
            target_side = "e" if side == "p" else "p"
            target_list = self.enemies if target_side == "e" else self.players
            tidx = action.get("target", 0)
            if tidx < 0 or tidx >= len(target_list) or not target_list[tidx]["alive"]:
                self.log.append(actor["name"] + " attacks invalid target")
            else:
                target = target_list[tidx]
                hit_roll = self.rng.randint(1, 20) + actor.get("atk", 0)
                ac = target.get("ac", 10)
                if self.terrain.get("cover") and target_side == "p":
                    ac += 2
                if self.terrain.get("high_ground") == side:
                    hit_roll += 2
                if hit_roll >= ac:
                    dmg = self.rng.randint(1, actor.get("dmg_die", 6)) + actor.get("dmg_bonus", 0)
                    if hit_roll - actor.get("atk", 0) == 20:
                        dmg *= 2
                        self.log.append("CRIT!")
                    resist = target.get("resist", {})
                    dtype = actor.get("dmg_type", "physical")
                    if dtype in resist:
                        dmg = int(dmg * (1 - resist[dtype]))
                    target["hp"] -= dmg
                    self.log.append(actor["name"] + " hits " + target["name"] + " for " + str(dmg))
                    if target["hp"] <= 0:
                        target["alive"] = False
                        self.log.append(target["name"] + " falls")
                        if target_side == "e":
                            self.loot.extend(target.get("drops", []))
                else:
                    self.log.append(actor["name"] + " misses " + target["name"])
        elif kind == "cast":
            spell = action.get("spell")
            cost = action.get("cost", 0)
            if actor.get("mp", 0) < cost:
                self.log.append(actor["name"] + " fizzles (no mp)")
            else:
                actor["mp"] -= cost
                if spell == "fireball":
                    for t in (self.enemies if side == "p" else self.players):
                        if t["alive"]:
                            dmg = self.rng.randint(10, 20)
                            if "fire" in t.get("resist", {}):
                                dmg = int(dmg * (1 - t["resist"]["fire"]))
                            t["hp"] -= dmg
                            self.log.append("fireball hits " + t["name"] + " for " + str(dmg))
                            if t["hp"] <= 0:
                                t["alive"] = False
                                if side == "p":
                                    self.loot.extend(t.get("drops", []))
                elif spell == "heal":
                    allies = self.players if side == "p" else self.enemies
                    tidx = action.get("target", idx)
                    tgt = allies[tidx]
                    heal = self.rng.randint(8, 16)
                    tgt["hp"] = min(tgt["max_hp"], tgt["hp"] + heal)
                    self.log.append(actor["name"] + " heals " + tgt["name"] + " for " + str(heal))
                elif spell == "poison_cloud":
                    for t in (self.enemies if side == "p" else self.players):
                        if t["alive"]:
                            t["status"].append({"kind": "poison", "power": 3, "duration": 3})
                            self.log.append(t["name"] + " is poisoned")
                else:
                    self.log.append("unknown spell " + str(spell))
        elif kind == "item":
            item = action.get("item")
            if item not in actor.get("inventory", {}):
                self.log.append(actor["name"] + " has no " + str(item))
            else:
                actor["inventory"][item] -= 1
                if actor["inventory"][item] <= 0:
                    del actor["inventory"][item]
                if item == "potion":
                    heal = 15
                    actor["hp"] = min(actor["max_hp"], actor["hp"] + heal)
                    self.log.append(actor["name"] + " drinks potion (+" + str(heal) + ")")
                elif item == "antidote":
                    actor["status"] = [s for s in actor["status"] if s["kind"] != "poison"]
                    self.log.append(actor["name"] + " uses antidote")
                elif item == "smoke_bomb":
                    self.terrain["cover"] = True
                    self.log.append("smoke fills the area")
                else:
                    self.log.append("unknown item " + str(item))
        elif kind == "flee":
            if side == "p":
                roll = self.rng.randint(1, 20)
                if roll >= 12:
                    self.phase = "fled"
                    self.log.append(actor["name"] + " flees successfully")
                    return
                else:
                    self.log.append(actor["name"] + " fails to flee")
            else:
                self.log.append("enemies don't flee")
        else:
            self.log.append("unknown action " + str(kind))
        self.turn += 1
        self._check_end()
        self._maybe_end_round()

    def _maybe_end_round(self):
        if self.turn > 0 and self.turn % len(self.initiative) == 0:
            self.round += 1
            self.log.append("round " + str(self.round))

    def _check_end(self):
        if not any(p["alive"] for p in self.players):
            self.phase = "defeat"
            self.log.append("party defeated")
        elif not any(e["alive"] for e in self.enemies):
            self.phase = "victory"
            self.log.append("victory! loot: " + str(self.loot))
```
