"""
Universal Demo Init
Works for ANY branch or bundle:
- item bundles
- character bundles
- world bundles
- symbolic bundles
- recursion bundles
- narrative bundles

Automatically:
1. Detects the current folder (considered the bundle).
2. Loads demo.py or demo_runner.py if present.
3. Initializes a minimal demo state.
4. Runs the demo safely with printed context.
"""

import os
import importlib
import traceback

def detect_demo_module():
    """
    Looks for demo.py or demo_runner.py in the current folder.
    Returns module name string or None.
    """
    candidates = ["demo", "demo_runner", "demo_run"]
    for name in candidates:
        if os.path.exists(f"{name}.py"):
            return name
    return None


def load_demo_module(module_name):
    """
    Loads the demo module by name.
    """
    try:
        return importlib.import_module(module_name)
    except Exception as e:
        print(f"[DEMO INIT] Failed to import {module_name}: {e}")
        traceback.print_exc()
        return None


def init_demo_state():
    """
    Universal minimal demo state.
    Extend this as your system grows.
    """
    return {
        "mode": "demo",
        "verbose": True,
        "context": {},
        "bundle_name": os.path.basename(os.getcwd()),
    }


def run_demo(module, state):
    """
    Attempts to run the demo using these common patterns:
    - run()
    - run_demo()
    - start()
    - main()
    - Demo().run()
    """
    if module is None:
        print("[DEMO INIT] No module provided to run.")
        return

    # Common entry points
    entry_points = ["run", "run_demo", "start", "main"]

    # Try direct functions
    for entry in entry_points:
        if hasattr(module, entry):
            print(f"[DEMO INIT] Running {entry}() …")
            try:
                getattr(module, entry)(state)
                return
            except Exception as e:
                print(f"[DEMO INIT] Error running {entry}(): {e}")
                traceback.print_exc()

    # Try class-based demos
    if hasattr(module, "Demo"):
        print("[DEMO INIT] Running Demo().run() …")
        try:
            d = module.Demo()
            if hasattr(d, "run"):
                d.run(state)
                return
        except Exception as e:
            print(f"[DEMO INIT] Error running Demo.run(): {e}")
            traceback.print_exc()

    print("[DEMO INIT] No executable demo entry point found.")


def init_demo():
    """
    Main entry for universal demo init.
    Detects module, loads state, executes demo.
    """
    print("\n===== UNIVERSAL DEMO INIT =====")

    bundle_name = os.path.basename(os.getcwd())
    print(f"[DEMO INIT] Bundle detected: {bundle_name}")

    module_name = detect_demo_module()
    if not module_name:
        print("[DEMO INIT] No demo module (demo.py or demo_runner.py) found.")
        return

    print(f"[DEMO INIT] Demo module detected: {module_name}")

    module = load_demo_module(module_name)
    state = init_demo_state()

    print("[DEMO INIT] Running demo with universal state…")
    run_demo(module, state)

    print("===== DEMO COMPLETE =====\n")


if __name__ == "__main__":
    init_demo()
