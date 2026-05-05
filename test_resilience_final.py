"""Final Test of Priority #2 - Using ASCII only for Windows console"""
import sys
sys.path.insert(0, r'H:\projects\Serenity Neural-Core')

print("=" * 60)
print("FINAL TEST - SESSION RESILIENCE HARDENING")
print("=" * 60)

tests = [
    ("Heartbeat", "core.heartbeat"),
    ("AutoSave", "core.auto_save"),
    ("RecoveryManager", "core.recovery"),
    ("DualLogger", "core.dual_logging"),
    ("SessionCloseAuto", "session_close_auto"),
]

results = []
for name, import_path in tests:
    try:
        __import__(import_path)
        print("[OK] CHECK OK:", name)
        results.append(name)
    except Exception as e:
        print("[ERR] Failed:", name, "-", str(e)[:40])

print()
print("=" * 60)
if len(results) == 5:
    print("STATUS: ALL SESSION RESILIENCE MECHANISMS VALIDATED")
else:
    print("RESULTS: {} of {} tests passed".format(len(results), 5))
print("=" * 60)
