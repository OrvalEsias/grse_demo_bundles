from loader import load_orchestration_bundle

def demo():
    char = {"name": "DemoCharacter", "traits": {"courage": 0.5}}
    bundle = load_orchestration_bundle()
    result = bundle["orchestrate"](char)
    print(result)

if __name__ == "__main__":
    demo()
