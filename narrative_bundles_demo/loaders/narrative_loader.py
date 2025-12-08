import json, os
def load_narrative(path):
    with open(path,'r') as f: return json.load(f)
