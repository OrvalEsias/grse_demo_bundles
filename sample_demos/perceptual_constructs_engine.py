# perceptual_constructs_engine.py
# A more detailed pipeline showing perception → features → symbol → understanding.

def perceptual_filter(input_text: str) -> dict:
    """Extract low-level perceptual features."""
    words = input_text.split()
    return {
        "raw": input_text,
        "word_count": len(words),
        "unique_words": len(set(words)),
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
    }

def generate_symbol(features: dict) -> str:
    """Map perceptual features into a symbolic category."""
    if features["word_count"] > 15:
        return "COMPLEX"
    if features["unique_words"] > 8:
        return "DIVERSE"
    if features["avg_word_length"] > 5:
        return "DENSE"
    return "SIMPLE"

def synthesize_understanding(symbol: str) -> str:
    """Produce an interpretation based on symbolic structure."""
    explanations = {
        "COMPLEX": "The perception contains many elements interacting together.",
        "DIVERSE": "The perception includes a wider range of concepts.",
        "DENSE": "The perception carries tightly-packed information.",
        "SIMPLE": "The perception is minimal and easy to integrate."
    }
    return explanations.get(symbol, "No interpretation available.")

def run_perceptual_demo():
    text = input("Enter a perception sample: ")
    f = perceptual_filter(text)
    sym = generate_symbol(f)
    understanding = synthesize_understanding(sym)

    print("\n--- RESULTS ---")
    print("Features:", f)
    print("Symbol:", sym)
    print("Understanding:", understanding)

if __name__ == "__main__":
    run_perceptual_demo()
