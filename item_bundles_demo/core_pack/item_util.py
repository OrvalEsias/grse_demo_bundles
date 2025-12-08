# item_util.py — DEMO STUB
# Full version loads item definitions, validates metadata, applies effects,
# handles world deltas, trait grants, fuzzy matching, etc.

def load_items():
    return {
        "module": __name__,
        "status": "stub",
        "items": {},
        "info": "Demo stub. Full version loads validated items.json, applies corrections, "
                "and returns canonical item definitions."
    }

def get_item(name, items=None):
    return {
        "module": __name__,
        "status": "stub",
        "requested": name,
        "info": "Item lookup stub. Fuzzy search + validator only in licensed engine."
    }

def apply_item_effects(character, world, item):
    return "Demo stub: effects not applied."

def pickup_item(character, item_name, items=None, location="demo"):
    return character, {}, f"[stub] picked up {item_name}", location

def use_item(character, world, item_name, items=None):
    return character, world, f"[stub] used {item_name}"
