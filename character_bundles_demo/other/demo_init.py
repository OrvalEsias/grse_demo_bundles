from .loader import load_branch

def demo_init():
    print("[demo_init] Loading branch modules...")
    modules = load_branch()
    print(f"[demo_init] Loaded {len(modules)} modules:")
    for name in modules:
        print(" -", name)
    return modules

if __name__ == "__main__":
    demo_init()
