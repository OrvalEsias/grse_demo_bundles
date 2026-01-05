from narrative_event_bus import NarrativeEventBus

bus = NarrativeEventBus()

def listener(event):
    print("Received event:", event)

bus.subscribe(listener)

bus.emit({"type": "quest_update", "value": "gate_opened"})
bus.emit({"type": "emotion", "tag": "fear"})
