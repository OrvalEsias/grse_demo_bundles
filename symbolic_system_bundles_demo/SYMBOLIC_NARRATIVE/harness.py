# harness.py
from loader import load_branch

def run_harness():
    system = load_branch()
    print(f"[HARNESS] {__package__} initialized:", system)

if __name__ == "__main__":
    run_harness()
