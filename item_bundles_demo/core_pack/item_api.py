# item_api.py — DEMO STUB
# Full version includes cooldowns, charges, symbolic hooks, feature pipeline,
# world deltas, session logging, and persistence.

def load_items():
    return {
        "module": __name__,
        "status": "stub",
        "info": "Items not loaded in demo. Full version loads items.json and "
                "supports symbolic hooks and corrections."
    }

def get_item(name, items=None):
    return {"name": name, "status": "stub"}

def pickup_item(character, item_name, items=None, location="demo"):
    return character, {}, f"[stub] {character.get('name','char')} picked up {item_name}", location

def use_item(character, world, item_name, items=None):
    return character, world, f"[stub] used {item_name}. Full engine applies trait, world, cooldown, and symbolic effects."
