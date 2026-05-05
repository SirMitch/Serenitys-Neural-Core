# tools/nav_helper.py
"""
Navigation helper for menu flows. Supports back(), home(), and graceful exit.
"""

class NavState:
    """Manages navigation history and state"""
    
    def __init__(self):
        self.history = ["HOME"]  # Stack of screens
        self.home_screen = "HOME"
    
    def push(self, screen: str):
        """Push new screen to stack"""
        self.history.append(screen)
    
    def pop(self):
        """Go back to previous screen"""
        if len(self.history) > 1:
            self.history.pop()
            return self.history[-1]
        return self.home_screen
    
    def home(self):
        """Reset to home"""
        self.history = [self.home_screen]
        return self.home_screen
    
    def current(self) -> str:
        """Get current screen"""
        return self.history[-1] if self.history else self.home_screen
    
    def can_go_back(self) -> bool:
        """Check if back is available"""
        return len(self.history) > 1


class NavigationError(Exception):
    """Raised to trigger navigation"""
    def __init__(self, action: str, screen: str = None):
        self.action = action  # 'back', 'home', 'exit'
        self.screen = screen
        super().__init__(f"NAV:{action}")
