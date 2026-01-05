# erbe_step_demo.py

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

if __name__ == "__main__":
    print(erbe_method_step(0.8, 0.7, 1.2))
