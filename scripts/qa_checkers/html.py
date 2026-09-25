"""html checker plugin — self-registering checker for HTML file validation.

Walks the cwd for *.html files (excluding pipeline directories), validates each
with html.parser.HTMLParser stack discipline (void tags whitelist, p excluded from
stack checking), and reports "N files checked, M invalid".

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


# Deterministic exclusions (fixed contract, no gitignore parsing)
EXCLUDE_DIRS = {
    ".git",
    ".pipeline",
    ".worktrees",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

# Void tags (self-closing, no closing tag needed)
VOID_TAGS = frozenset((
    "br", "hr", "img", "input", "meta", "link", "area", "base",
    "col", "embed", "source", "track", "wbr",
))

# Tags excluded from stack checking (implicit close is legal in HTML)
NO_STACK_TAGS = frozenset(("p",))


class StackParser(HTMLParser):
    """HTML parser that validates tag stack discipline."""
    
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.reason: str = ""
    
    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Handle opening tags."""
        if tag not in VOID_TAGS and tag not in NO_STACK_TAGS:
            self.stack.append(tag)
    
    def handle_endtag(self, tag: str) -> None:
        """Handle closing tags."""
        if tag in VOID_TAGS or tag in NO_STACK_TAGS:
            return
        
        if not self.stack:
            if not self.reason:
                self.reason = f"mismatch: unexpected </{tag}> (stack empty)"
            return
        
        if tag == self.stack[-1]:
            self.stack.pop()
            return
        
        if tag in self.stack:
            # Implicit close: the close tag sits deeper in the stack, so all
            # tags above it were never closed explicitly.
            if not self.reason:
                self.reason = f"unclosed {self.stack[-1]}"
            while self.stack:
                if self.stack.pop() == tag:
                    break
            return
        
        if not self.reason:
            self.reason = f"mismatch: expected </{self.stack[-1]}> got </{tag}>"


def html_check() -> tuple[str, int]:
    """Validate all HTML files in cwd and return compressed output.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    cwd = Path.cwd()
    
    # Find all *.html files
    html_files = []
    for html_file in cwd.rglob("*.html"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in html_file.relative_to(cwd).parts):
            continue
        html_files.append(html_file)
    
    # Sort for determinism
    html_files.sort()
    
    total = len(html_files)
    invalid_files = []
    
    for html_file in html_files:
        try:
            with open(html_file, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            
            parser = StackParser()
            parser.feed(text)
            parser.close()
            
            # Check for validation errors
            reason = parser.reason
            if not reason and parser.stack:
                reason = f"unclosed {parser.stack[-1]}"
            
            if reason:
                rel_path = html_file.relative_to(cwd)
                invalid_files.append((str(rel_path), reason))
        
        except Exception as e:
            rel_path = html_file.relative_to(cwd)
            invalid_files.append((str(rel_path), "parse error"))
    
    compressed = f"{total} files checked, {len(invalid_files)} invalid\n"
    
    if invalid_files:
        compressed += "## failed_files\n"
        for path, reason in invalid_files[-20:]:  # Last 20
            compressed += f"INVALID {path} ({reason})\n"
        return compressed, 1
    
    return compressed, 0


# Self-register with the qa_compress registry
import sys
from pathlib import Path as PathlibPath

script_dir = PathlibPath(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("html", html_check)
