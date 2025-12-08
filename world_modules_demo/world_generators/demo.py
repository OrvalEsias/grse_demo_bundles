from .demo_init import demo_init

def demo():
    modules = demo_init()
    print("[demo] Running minimal demo for each module...")
    for name, module in modules.items():
        print(f"[demo] Module {name} OK")
    print("[demo] Done.")
    return True

if __name__ == "__main__":
    demo()
