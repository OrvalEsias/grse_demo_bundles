# mini_symbolic_engine.py

class MiniEngine:
    def __init__(self):
        self.state = {"energy": 1.0, "clarity": 0.5}
    
    def tick(self, intent: float):
        # symbolic dynamics
        self.state["energy"] += intent * 0.1
        self.state["clarity"] = (
            self.state["clarity"] * 0.9 + (self.state["energy"] / 2) * 0.1
        )
        return self.state

if __name__ == "__main__":
    engine = MiniEngine()
    for step in range(5):
        print(engine.tick(intent=0.3))
