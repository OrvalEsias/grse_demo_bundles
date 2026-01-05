# narrative_event_bus.py
from typing import List, Callable, Dict, Any

class NarrativeEventBus:
    def __init__(self):
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, fn: Callable[[Dict[str, Any]], None]):
        self.subscribers.append(fn)

    def emit(self, event: Dict[str, Any]):
        for fn in self.subscribers:
            fn(event)
