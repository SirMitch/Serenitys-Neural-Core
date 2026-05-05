"""Serenity Internal Intelligence Interface — Minimal"""

from core.control_center import ControlCenter

class SerenityInternalInterface:
    def connect_all_services(self):
        print("[Serenity Agent] Connected")
        return self

def get_internal_developer():
    return SerenityInternalInterface()

def is_inside_out_mode_active():
    return True
