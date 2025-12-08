from narrative_branch.engines import *
def load_system():
    return {
        "quest": QuestManager(),
        "mythic": MythicCycleEngine(),
        "blackboard": NarrativeBlackboard(),
        "events": NarrativeEventBus(),
        "cut": CutsceneEngine()
    }
