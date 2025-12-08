
from .demo_init import demo_init
from .demo import demo
from .full_run import full_run

def harness():
    print("[harness] Starting harness...")
    demo_init()
    demo()
    full_run()
    print("[harness] Success.")
    return True

if __name__=="__main__":
    harness()

