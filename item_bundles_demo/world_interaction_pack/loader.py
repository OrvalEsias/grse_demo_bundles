import importlib, os

def load_branch(path=None):
    if path is None:
        path=os.path.dirname(__file__)
    modules={}
    for fname in os.listdir(path):
        if fname.endswith(".py") and fname not in ["loader.py","__init__.py"]:
            mod=fname[:-3]
            try:
                modules[mod]=importlib.import_module(f"{__package__}.{mod}")
            except Exception as e:
                print(f"[Loader] Failed {mod}: {e}")
    return modules
