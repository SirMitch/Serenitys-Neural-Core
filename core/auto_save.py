"""Serenity Auto-Save — Micro-commits & Change Staging"""

import sys, os, hashlib, time
from pathlib import Path#

class AutoSave:
    """Handles frequent automatic micro-commits and staging of changes"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent.parent
        self.staging_dir = self.root / ".auto_staging"
        self.recovery_log = self.root / "session_logs" / "recovery.log"
        self.staging_dir.mkdir(exist_ok=True)
        self.recovery_log.parent.mkdir(exist_ok=True)
        
    def hash_file(self, filepath):
        """Compute SHA-256 hash of file"""
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    
    def detect_altered_files(self):
        """Auto-detect altered files via hash comparison"""
        altered = []
        # Scan key directories
        for ext in ['*.py', '*.md', '*.txt', '*.json', '*.toml']:
            for f in self.root.rglob(ext):
                if '.git' in f.parts or 'backups' in f.parts:
                    continue
                # Simple mtime check (could be enhanced with stored hashes)
                if f.stat().st_mtime > time.time() - 300:  # modified in last 5 min
                    altered.append(f)
        return altered
    
    def micro_commit(self, files=None, message="Auto-save micro-commit"):
        """Perform automatic micro-commit of changes"""
        import subprocess
        if files is None:
            files = self.detect_altered_files()
        if not files:
            return False
        try:
            # Stage files
            for f in files:
                subprocess.run(['git', 'add', str(f)], cwd=str(self.root))
            # Commit
            subprocess.run(['git', 'commit', '-m', message], cwd=str(self.root))
            # Log to recovery log
            with open(self.recovery_log, 'a') as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Micro-commit: {len(files)} files modified\n")
            return True
        except Exception as e:
            print(f"[AutoSave] Error: {e}")
            return False
    
    def stage_for_recovery(self, filepath):
        """Stage a file for recovery (copy to staging area)"""
        dest = self.staging_dir / Path(filepath).name
        try:
            import shutil
            shutil.copy2(filepath, dest)
            return True
        except Exception as e:
            print(f"[AutoSave] Staging failed: {e}")
            return False

def main():
    auto = AutoSave()
    altered = auto.detect_altered_files()
    print(f"[AutoSave] Detected {len(altered)} altered files")
    if altered:
        auto.micro_commit(altered)

if __name__ == "__main__":
    main()
