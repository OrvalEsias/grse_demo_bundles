from .demo_init import demo_init
from .demo import demo
from .full_run import full_run

def harness():
    print("[harness] Starting test harness...")
    demo_init()
    demo()
    full_run()
    print("[harness] All tests passed (no exceptions).")
    return True

if __name__ == "__main__":
    harness()
