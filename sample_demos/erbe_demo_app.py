# erbe_demo_app.py
import gradio as gr

# --- Toy ERBE Step Demo (safe to share) ---
def erbe_method_step(will, perception, field):
    filtered_input = perception * field
    symbol = will * filtered_input
    understanding = symbol / (1 + field)
    expression = understanding * 0.9
    updated_field = field + (expression - field) * 0.1
    
    return {
        "coherence": understanding,
        "expression": expression,
        "updated_field": updated_field
    }

# --- Gradio Wrapper ---
def run_step(will, perception, field):
    return erbe_method_step(will, perception, field)

demo = gr.Interface(
    fn=run_step,
    inputs=[
        gr.Slider(0, 2, value=0.8, label="Will"),
        gr.Slider(0, 2, value=0.7, label="Perception"),
        gr.Slider(0, 2, value=1.0, label="Field Strength"),
    ],
    outputs="json",
    title="Erbe System – Symbolic Step Demo (Toy Version)",
    description="A simple, safe demonstration of a symbolic update step. Not part of the full engine."
)

if __name__ == "__main__":
    demo.launch()
