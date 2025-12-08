# harness.py
try:
    from loader import load_branch
except ImportError:
    load_branch = None

try:
    from run import run
except ImportError:
    run = None

def run_harness():
    print(f"[HARNESS] Running harness for branch: {__package__}")

    system = None
    if callable(load_branch):
        try:
            system = load_branch()
            print("[HARNESS] System initialized.")
        except Exception as e:
            print("[HARNESS] Failed to initialize system:", e)
    else:
        print("[HARNESS] No 'load_branch' found.")

    if callable(run):
        try:
            result = run()
            print("[HARNESS] Run output:", result)
        except Exception as e:
            print("[HARNESS] Failed running 'run':", e)
    else:
        print("[HARNESS] No 'run' function found.")

    return system

if __name__ == "__main__":
    run_harness()
 
 - 