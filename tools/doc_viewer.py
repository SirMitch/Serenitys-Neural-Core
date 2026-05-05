# tools/doc_viewer.py
"""
Dynamic documentation viewer with smart navigation.
Scans root/docs directory, displays available documents, and provides
full interactive help system integrated into main menu.
"""

from pathlib import Path
from logging_helper import Logger
from nav_helper import NavState

logger: Logger = None
nav: NavState = None

def set_logger(log_obj: Logger):
    global logger
    logger = log_obj

def set_nav(nav_obj: NavState):
    global nav
    nav_obj

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BRIGHT_WHITE = "\033[97m"

def cprint(text: str, color=Colors.RESET, bold: bool = False):
    """Print colored text"""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")

def clear_screen():
    """Clear terminal"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def get_docs_directory(script_root: Path) -> Path:
    """Find docs directory relative to script root"""
    docs_dir = script_root / "docs"
    
    if not docs_dir.exists():
        if logger:
            logger.warning(f"Docs directory not found: {docs_dir}", "DOCVIEWER")
        return None
    
    if logger:
        logger.debug(f"Found docs directory: {docs_dir}", "DOCVIEWER")
    
    return docs_dir

def scan_documents(docs_dir: Path) -> dict:
    """
    Scan docs directory for documentation files.
    Returns dict: {filename: full_path}
    """
    if not docs_dir:
        return {}
    
    docs = {}
    extensions = {'.md', '.txt'}
    
    try:
        for file in sorted(docs_dir.iterdir()):
            if file.is_file() and file.suffix in extensions:
                # Skip internal files
                if file.name.startswith('_'):
                    continue
                docs[file.name] = file
        
        if logger:
            logger.info(f"Scanned {len(docs)} documentation files", "DOCVIEWER")
        
        return docs
    
    except Exception as e:
        if logger:
            logger.error(f"Failed to scan docs: {str(e)}", "DOCVIEWER")
        return {}

def categorize_documents(docs: dict) -> dict:
    """
    Categorize documents by type (Getting Started, Guides, Reference, etc).
    Returns dict: {category: [files]}
    """
    categories = {
        "Getting Started": [],
        "Guides": [],
        "Reference": [],
        "Troubleshooting": [],
        "Other": []
    }
    
    # Categorization rules
    keywords = {
        "Getting Started": ["START", "QUICK", "README"],
        "Guides": ["GUIDE", "HOW", "MANUAL"],
        "Reference": ["REFERENCE", "API", "IMPLEMENTATION", "MANIFEST"],
        "Troubleshooting": ["TROUBLE", "DEBUG", "ERROR", "ISSUE"],
    }
    
    for filename in docs:
        upper_name = filename.upper()
        categorized = False
        
        for category, keywords_list in keywords.items():
            if any(kw in upper_name for kw in keywords_list):
                categories[category].append(filename)
                categorized = True
                break
        
        if not categorized:
            categories["Other"].append(filename)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def read_document(file_path: Path) -> str:
    """Read document file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if logger:
            logger.debug(f"Read document: {file_path.name}", "DOCVIEWER")
        
        return content
    
    except Exception as e:
        if logger:
            logger.error(f"Failed to read {file_path.name}: {str(e)}", "DOCVIEWER")
        return f"Error reading file: {str(e)}"

def paginate_text(text: str, lines_per_page: int = 20) -> list:
    """Split text into pages for display"""
    text_lines = text.split('\n')
    pages = []
    
    for i in range(0, len(text_lines), lines_per_page):
        pages.append('\n'.join(text_lines[i:i + lines_per_page]))
    
    return pages if pages else ["(empty file)"]

def show_doc_viewer(script_root: Path) -> str:
    """
    Main documentation viewer interface.
    Returns: 'back' to return to main menu, 'exit' to quit
    """
    docs_dir = get_docs_directory(script_root)
    
    if not docs_dir:
        clear_screen()
        cprint("="*80, Colors.RED)
        cprint("DOCUMENTATION SYSTEM", Colors.RED, bold=True)
        cprint("="*80, Colors.RED)
        print()
        cprint("✗ Documentation directory not found", Colors.RED)
        cprint(f"  Expected location: {script_root / 'docs'}", Colors.YELLOW)
        print()
        cprint("To use this feature, create root\\docs\\ and add documentation files (.md, .txt)", Colors.YELLOW)
        print()
        input("Press Enter to return to main menu...")
        return "back"
    
    docs = scan_documents(docs_dir)
    
    if not docs:
        clear_screen()
        cprint("="*80, Colors.RED)
        cprint("DOCUMENTATION SYSTEM", Colors.RED, bold=True)
        cprint("="*80, Colors.RED)
        print()
        cprint("✗ No documentation files found", Colors.RED)
        cprint(f"  Checked: {docs_dir}", Colors.YELLOW)
        print()
        cprint("Documentation files should have .md or .txt extension", Colors.YELLOW)
        print()
        input("Press Enter to return to main menu...")
        return "back"
    
    categories = categorize_documents(docs)
    
    if logger:
        logger.info(f"Documentation system ready ({len(docs)} files)", "DOCVIEWER")
    
    return show_doc_menu(docs, categories, docs_dir)

def show_doc_menu(docs: dict, categories: dict, docs_dir: Path) -> str:
    """Show main documentation menu"""
    while True:
        clear_screen()
        cprint("="*80, Colors.MAGENTA)
        cprint("DOCUMENTATION & GUIDES", Colors.MAGENTA, bold=True)
        cprint("="*80, Colors.MAGENTA)
        print()
        
        cprint(f"Available Documents: {len(docs)}", Colors.CYAN, bold=True)
        print()
        
        # Show by category
        choice_map = {}
        choice_num = 1
        
        for category, files in categories.items():
            cprint(f" ── {category} ──", Colors.CYAN, bold=True)
            for filename in files:
                cprint(f"  {choice_num}) {filename}", Colors.BRIGHT_WHITE)
                choice_map[str(choice_num)] = (filename, docs[filename])
                choice_num += 1
            print()
        
        cprint("  B) Back to Main Menu", Colors.YELLOW)
        cprint("  Q) Quit Program", Colors.YELLOW)
        print()
        
        try:
            choice = input(f"{Colors.YELLOW}Select document or option: {Colors.RESET}").strip()
            
            if choice.upper() == "Q":
                if logger:
                    logger.info("User quit from documentation viewer", "DOCVIEWER")
                return "exit"
            
            if choice.upper() == "B":
                if logger:
                    logger.info("User returned to main menu from docs", "DOCVIEWER")
                return "back"
            
            if choice in choice_map:
                filename, filepath = choice_map[choice]
                show_document(filename, filepath)
            else:
                cprint("Invalid choice", Colors.YELLOW)
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            if logger:
                logger.info("User interrupted documentation viewer", "DOCVIEWER")
            return "exit"
        except Exception as e:
            if logger:
                logger.error(f"Menu error: {str(e)}", "DOCVIEWER")
            cprint(f"Error: {str(e)}", Colors.RED)
            input("Press Enter to continue...")

def show_document(filename: str, filepath: Path) -> str:
    """Display document with paging"""
    content = read_document(filepath)
    pages = paginate_text(content, lines_per_page=18)
    current_page = 0
    
    while True:
        clear_screen()
        cprint("="*80, Colors.CYAN)
        cprint(f"DOCUMENT: {filename}", Colors.CYAN, bold=True)
        cprint("="*80, Colors.CYAN)
        print()
        
        # Show current page
        print(pages[current_page])
        
        print()
        cprint("─"*80, Colors.GRAY)
        
        # Navigation info
        page_info = f"Page {current_page + 1} of {len(pages)}"
        cprint(page_info, Colors.GRAY)
        
        print()
        
        # Navigation options
        options = []
        if current_page > 0:
            options.append("P) Previous")
        if current_page < len(pages) - 1:
            options.append("N) Next")
        options.extend(["B) Back to Docs Menu", "Q) Quit"])
        
        for opt in options:
            cprint(f"  {opt}", Colors.YELLOW)
        
        print()
        
        try:
            choice = input(f"{Colors.YELLOW}Choose: {Colors.RESET}").strip().upper()
            
            if choice == "Q":
                if logger:
                    logger.info("User quit from document", "DOCVIEWER")
                return "exit"
            
            if choice == "B":
                if logger:
                    logger.debug(f"User closed document: {filename}", "DOCVIEWER")
                return "back"
            
            if choice == "N" and current_page < len(pages) - 1:
                current_page += 1
            elif choice == "P" and current_page > 0:
                current_page -= 1
            else:
                cprint("Invalid choice", Colors.YELLOW)
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            if logger:
                logger.info("User interrupted document", "DOCVIEWER")
            return "exit"
        except Exception as e:
            if logger:
                logger.error(f"Document display error: {str(e)}", "DOCVIEWER")
            cprint(f"Error: {str(e)}", Colors.RED)
            input("Press Enter to continue...")

def get_documentation_summary(script_root: Path) -> str:
    """Get summary of available documentation"""
    docs_dir = get_docs_directory(script_root)
    
    if not docs_dir:
        return "No documentation found"
    
    docs = scan_documents(docs_dir)
    
    if not docs:
        return "No documentation files found"
    
    return f"{len(docs)} documentation files available"
