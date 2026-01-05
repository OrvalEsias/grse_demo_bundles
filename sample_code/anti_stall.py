# engine/anti_stall.py
from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple, Any

# Pool of contrastive markers we can inject to break loops
FORCE_MARKERS_POOL: List[str] = [
    "echo_marker", "glyph_touched", "signal_carrier", "true_name", "recursion_loop",
    "mirror_trace", "broadcast_signal", "memory_link"
]

# Preferred “jolt” items to nudge state
JOLT_ITEMS: List[str] = ["glyphstone", "mirror_wand", "glyph_of_insight"]


class AntiStall:
    """
    Detects tight cycles and intervenes:
      1) rotates zones (prefers unlocked, different-energy zones)
      2) optionally auto-uses a 'jolt' item on the zone
      3) injects contrasting markers
      4) queues 1–2 prompts to steer next tick

    A cooldown prevents back-to-back interventions.

    Returns from assess_and_intervene:
        (char, world, markers, queued_prompts, note)
    """

    def __init__(
        self,
        window: int = 6,
        min_repeats: int = 3,
        cooldown: int = 2,
        prefer_items: Optional[List[str]] = None,
        rng: Optional[random.Random] = None,
    ):
        self.window = int(window)
        self.min_repeats = int(min_repeats)
        self.cooldown = int(cooldown)
        self.prefer_items = list(prefer_items or JOLT_ITEMS)
        self._buf: Deque[Tuple[str, str]] = deque(maxlen=self.window)
        self._cooldown_left = 0
        self._recent_forced: Deque[str] = deque(maxlen=8)
        self._rng = rng or random.Random()

    # -------- internals --------
    def _sig(self, intent: Any, zone: Any) -> Tuple[str, str]:
        i = (intent or "neutral")
        if isinstance(i, (list, tuple)):
            i = ",".join(map(str, i))
        return (str(i).lower(), str(zone or "dream_gate"))

    def _is_stuck(self) -> bool:
        """Consecutive repeats OR only 1–2 unique signatures across the window."""
        if not self._buf:
            return False
        last = self._buf[-1]

        # Count consecutive repeats from the end
        consec = 1
        for prev in list(self._buf)[-2::-1]:
            if prev == last:
                consec += 1
            else:
                break

        unique = len(set(self._buf))
        return consec >= self.min_repeats or (len(self._buf) >= self.window and unique <= 2)

    def _zone_energy(self, world: Dict, z: str) -> float:
        try:
            zinfo = (world.get("zones", {}) or {}).get(z, {}) or {}
            return float(zinfo.get("energy", zinfo.get("symbolic_density", 0.0)) or 0.0)
        except Exception:
            return 0.0

    def _pick_other_zone(self, world: Dict, cur: str) -> Optional[str]:
        zones = world.get("zones", {})
        if not isinstance(zones, dict) or not zones:
            return None

        zlist = [z for z in zones.keys() if z != cur]
        if not zlist:
            return None

        # Prefer unlocked
        unlocked = [z for z in zlist if not (zones.get(z, {}) or {}).get("locked")]
        cand = unlocked or zlist

        # Pick farthest energy from current to maximize contrast
        cur_e = self._zone_energy(world, cur)
        cand.sort(key=lambda z: abs(self._zone_energy(world, z) - cur_e), reverse=True)
        return cand[0] if cand else None

    def _force_markers(self, detected: List[str]) -> List[str]:
        current = set(detected or [])
        pool = [m for m in FORCE_MARKERS_POOL if m not in current and m not in self._recent_forced]
        if not pool:
            pool = FORCE_MARKERS_POOL[:]  # recycle if we exhausted options
        k = min(2, len(pool))
        pick = self._rng.sample(pool, k=k) if k > 0 else []
        for m in pick:
            self._recent_forced.append(m)
        return list(detected or []) + pick

    def _safe_pickup(self, item_engine, char: Dict, item: str, items_db: Dict, location: Optional[str] = None):
        """
        Call pickup_item with tolerant signature handling:
        - pickup_item(char, name, items_db)
        - pickup_item(char, name, items_db, location=...)
        Returns (char, note_or_None)
        """
        if not item_engine:
            return char, None
        try:
            # Newer signature with location
            if location is not None:
                char2, _w2, _msg, _loc = item_engine.pickup_item(char, item, items_db, location=location)
            else:
                # Legacy signature
                char2, _w2, _msg, _loc = item_engine.pickup_item(char, item, items_db)
            return char2 or char, "picked"
        except TypeError:
            # Try legacy again without tuple unpacking
            try:
                char2 = item_engine.pickup_item(char, item, items_db)
                return char2 or char, "picked"
            except Exception:
                return char, None
        except Exception:
            return char, None

    def _try_jolt_item(self, char: Dict, world: Dict, item_engine, items_db) -> Optional[str]:
        if not item_engine or not items_db:
            return None

        inv = list(char.get("inventory", []) or [])
        zone_name = str(char.get("zone", "dream_gate"))

        # Prefer inventory; otherwise pick up from the zone if present
        chosen = None
        for it in self.prefer_items:
            if it in inv:
                chosen = it
                break

        if chosen is None:
            zinfo = (world.get("zones", {}).get(zone_name, {}) or {})
            zitems = zinfo.get("items", []) or []
            for it in self.prefer_items:
                if it in zitems:
                    char, _ = self._safe_pickup(item_engine, char, it, items_db, location=zone_name)
                    chosen = it
                    break

        if not chosen:
            return None

        try:
            # use_item(char, world, name, items_db, target=..., target_type=...)
            _char2, _world2, msg = item_engine.use_item(
                char, world, chosen, items_db, target=zone_name, target_type="zone"
            )
            return msg
        except Exception:
            return None

    # -------- public API --------
    def seed(self, seed_value: int) -> None:
        """Deterministic behavior for tests."""
        self._rng.seed(seed_value)

    def assess_and_intervene(
        self,
        char: Dict,
        world: Dict,
        detected_markers: Optional[List[str]],
        intent: Any,
        *,
        item_engine=None,
        items_db: Optional[Dict] = None
    ) -> Tuple[Dict, Dict, List[str], List[str], Optional[str]]:
        """
        Evaluate recent behavior; if stalled, intervene.

        Args:
            char, world: current states
            detected_markers: markers detected this tick (will be augmented)
            intent: current intent (str or list)
            item_engine, items_db: optional item system

        Returns:
            (char, world, markers, queued_prompts, note)
        """
        markers = list(detected_markers or [])
        zone = str(char.get("zone", "dream_gate"))

        # Track signature
        self._buf.append(self._sig(intent, zone))

        # Respect cooldown
        if self._cooldown_left > 0:
            self._cooldown_left -= 1
            return char, world, markers, [], None

        # If not stuck, no intervention
        if not self._is_stuck():
            return char, world, markers, [], None

        # --- Interventions ---
        note_parts: List[str] = []

        # 1) rotate zones
        nz = self._pick_other_zone(world, zone)
        if nz and nz != zone:
            char["zone"] = nz
            markers.append("zone_shift")
            note_parts.append(f"zone→{nz}")

        # 2) item jolt (optional)
        jolt_note = self._try_jolt_item(char, world, item_engine, items_db)
        if jolt_note:
            note_parts.append("jolt_item")

        # 3) inject contrasting markers
        before = set(markers)
        markers = self._force_markers(markers)
        added = [m for m in markers if m not in before]
        if added:
            note_parts.append("markers+" + ",".join(added))

        # 4) queue nudging prompts
        target_zone = char.get("zone", nz or zone)
        queued = []
        for s in ("attune_self", "activate_glyph", f"enter zone:{target_zone}"):
            if s not in queued:
                queued.append(s)

        # cooldown so we don't hammer every tick
        self._cooldown_left = self.cooldown
        note = " | ".join(note_parts) if note_parts else "intervened"

        # Optional: drop a tiny log for downstream observers
        try:
            char.setdefault("_logs", []).append(f"[AntiStall] {note}")
        except Exception:
            pass

        return char, world, markers, queued, note
