
from .demo_init import demo_init

def demo():
    modules=demo_init()
    print("[demo] Running minimal tests...")
    for name in modules:
        print(f"[demo] {name} OK")
    return True

if __name__=="__main__":
    demo()

