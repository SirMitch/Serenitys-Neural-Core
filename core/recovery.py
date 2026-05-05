"""Serenity Recovery — Session Interruption Recovery"""

import sys, os, hashlib, time
from pathlib import Path#

class RecoveryManager:
    """Detects unsaved/altered work and offers safe recovery"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent.parent
        self.recovery_log = self.root / "session_logs" / "recovery.log"
        self.hash_store = self.root / "session_logs" / "file_hashes.json"
        self.recovery_log.parent.mkdir(parents=True, exist_ok=True)
        
    def compute_hash(self, filepath):
        """Compute SHA-256 hash of file"""
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None
    
    def scan_and_compare(self):
        """Scan key files and compare with stored hashes"""
        import json
        # Load stored hashes
        if self.hash_store.exists():
            with open(self.hash_store, 'r') as f:
                stored = json.load(f)
        else:
            stored = {}
        
        altered = []  
        # Scan key directories
        for pattern in ['*.py', '*.md', '*.txt', '*.json', '*.toml']:
            for f in self.root.rglob(pattern):
                if '.git' in f.parts or 'backups' in f.parts:
                    continue
                current_hash = self.compute_hash(f)
                stored_hash = stored.get(str(f))
                if current_hash and stored_hash and current_hash != stored_hash:
                    altered.append(f)
        return altered
    
    def update_hashes(self):
        """Update stored hashes after commit"""
        import json
        hashes = {}
        for pattern in ['*.py', '*.md', '*.txt', '*.json', '*.toml']:
            for f in self.root.rglob(pattern):
                if '.git' in f.parts or 'backups' in f.parts:
                    continue
                h = self.compute_hash(f)
                if h:
                    hashes[str(f)] = h
        with open(self.hash_store, 'w') as f:
            json.dump(hashes, f, indent=2)
    
    def attempt_recovery(self):
        """Attempt recovery of unsaved work"""
        altered = self.scan_and_compare()
        if not altered:
            print("[Recovery] No unsaved changes detected")
            return False
        
        print(f"[Recovery] Detected {len(altered)} altered files:")
        for f in altered[:5]:
            print(f"  - {f.name}")
        
        # Log recovery attempt
        with open(self.recovery_log, 'a') as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Recovery triggered: {len(altered)} files altered\n")
        
        # Option: auto-stage for commit
        import subprocess
        for f in altered:
            subprocess.run(['git', 'add', str(f)], cwd=str(self.root))
        
        print("[Recovery] Files staged for commit. Review and commit when ready.")
        return True

def main():
    rm = RecoveryManager()
    if rm.attempt_recovery():
        print("[Recovery] Safe recovery mode activated")

if __name__ == "__main__":
    main()
