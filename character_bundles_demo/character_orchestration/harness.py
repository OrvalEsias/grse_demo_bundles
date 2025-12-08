from loader import load_orchestration_bundle

def test_orchestration():
    bundle = load_orchestration_bundle()
    result = bundle["orchestrate"]({"name": "TestChar"})
    print("Orchestration OK:", result)

if __name__ == "__main__":
    test_orchestration()
