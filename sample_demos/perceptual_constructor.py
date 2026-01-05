# perceptual_constructor.py

class PerceptualConstructor:
    def __init__(self):
        self.state = 0.0
    
    def ingest(self, signal):
        self.state = 0.7 * self.state + 0.3 * signal
        return self.state
    
    def symbolize(self):
        return {"symbol": self.state ** 2}
    
    def step(self, signal):
        new_state = self.ingest(signal)
        symbol = self.symbolize()
        return {"state": new_state, "symbol": symbol}


if __name__ == "__main__":
    pc = PerceptualConstructor()
    for s in [0.4, 0.6, 0.9]:
        print(pc.step(s))
