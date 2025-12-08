import importlib
import os

def load_branch(path=None):
    if path is None:
        path = os.path.dirname(__file__)
    modules = {}
    for fname in os.listdir(path):
        if fname.endswith(".py") and fname not in ["loader.py", "__init__.py"]:
            modname = fname[:-3]
            try:
                module = importlib.import_module(f"{__package__}.{modname}")
                modules[modname] = module
            except Exception as e:
                print(f"[Loader] Failed to load {modname}: {e}")
    return modules
