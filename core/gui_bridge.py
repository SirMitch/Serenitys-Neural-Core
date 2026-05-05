"""Serenity GUI Bridge — Minimal Interface"""

class LogStreamer:
    def subscribe(self, session_id):
        return {"subscription_id": f"sub_{session_id}"}

class ModuleActivityVisualizer:
    pass

class StateDiffDisplay:
    pass

def init_gui_bridge():
    return {"log_streamer": LogStreamer()}
