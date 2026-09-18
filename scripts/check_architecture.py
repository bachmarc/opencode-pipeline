#!/usr/bin/env python3
"""Check architecture rules for src/core/ modules.

Uses Python AST to parse all .py files and check imports against an allowlist.
Default allowlist: Python stdlib modules.
Custom allowlist: one module per line in a file.

Exit codes:
  0 - PASS: all imports are allowed
  1 - FAIL: forbidden imports found
"""

import ast
import json
import sys
import sysconfig
from pathlib import Path
from typing import Dict, List, Set, Tuple


def get_stdlib_modules() -> Set[str]:
    """Get set of Python standard library module names."""
    # Get stdlib path
    stdlib_path = sysconfig.get_path("stdlib")
    platstdlib_path = sysconfig.get_path("platstdlib")
    
    stdlib_modules = set()
    
    # Add built-in modules
    stdlib_modules.update(sys.builtin_module_names)
    
    # Add modules from stdlib directory
    if stdlib_path:
        stdlib_dir = Path(stdlib_path)
        if stdlib_dir.exists():
            for item in stdlib_dir.iterdir():
                if item.is_file() and item.suffix == '.py':
                    stdlib_modules.add(item.stem)
                elif item.is_dir() and not item.name.startswith('_'):
                    stdlib_modules.add(item.name)
    
    # Add common stdlib modules that might not be in the directory
    common_stdlib = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
        'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
        'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
        'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
        'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
        'dis', 'distutils', 'doctest', 'dummy_thread', 'dummy_threading', 'email',
        'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp',
        'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
        'getpass', 'gettext', 'glob', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html',
        'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io',
        'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale',
        'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
        'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis',
        'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
        'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
        'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats',
        'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random',
        're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
        'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
        'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
        'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
        'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
        'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
        'tracemalloc', 'tty', 'turtle', 'types', 'typing', 'typing_extensions', 'unicodedata',
        'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
        'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
        'zipapp', 'zipfile', 'zipimport', 'zlib',
    }
    stdlib_modules.update(common_stdlib)
    
    return stdlib_modules


def load_allowlist(allowlist_file: Path) -> Set[str]:
    """Load custom allowlist from file (one module per line)."""
    allowlist = set()
    try:
        with open(allowlist_file, 'r', encoding='utf-8') as f:
            for line in f:
                module = line.strip()
                if module and not module.startswith('#'):
                    allowlist.add(module)
    except Exception as e:
        print(json.dumps({
            "result": "FAIL",
            "error": f"Error reading allowlist: {e}"
        }))
        sys.exit(1)
    return allowlist


def extract_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Extract all import statements from a Python file.
    
    Returns list of (module_name, line_number) tuples.
    """
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception:
        # Skip files that can't be parsed
        return imports
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Get the top-level module name
                module_name = alias.name.split('.')[0]
                imports.append((module_name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Get the top-level module name
                module_name = node.module.split('.')[0]
                imports.append((module_name, node.lineno))
    
    return imports


def check_architecture(src_core_path: Path, allowlist: Set[str]) -> Tuple[bool, List[Dict]]:
    """Check all Python files in src/core/ for forbidden imports.
    
    Returns (is_clean, list_of_violations).
    """
    violations = []
    
    if not src_core_path.exists():
        return False, [{"error": f"Path not found: {src_core_path}"}]
    
    # Find all .py files
    py_files = list(src_core_path.rglob("*.py"))
    
    for py_file in py_files:
        imports = extract_imports(py_file)
        
        for module_name, line_no in imports:
            if module_name not in allowlist:
                violations.append({
                    "file": str(py_file.relative_to(src_core_path.parent)),
                    "import": module_name,
                    "line": line_no
                })
    
    is_clean = len(violations) == 0
    return is_clean, violations


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "result": "FAIL",
            "error": "Usage: check_architecture.py <src-core-path> [--allowlist <file>]"
        }))
        sys.exit(1)
    
    src_core_path = Path(sys.argv[1])
    
    # Get default allowlist (stdlib)
    allowlist = get_stdlib_modules()
    
    # Check for custom allowlist
    if len(sys.argv) >= 4 and sys.argv[2] == "--allowlist":
        allowlist_file = Path(sys.argv[3])
        custom_allowlist = load_allowlist(allowlist_file)
        allowlist.update(custom_allowlist)
    
    # Check architecture
    is_clean, violations = check_architecture(src_core_path, allowlist)
    
    if is_clean:
        # Count files checked
        py_files = list(src_core_path.rglob("*.py"))
        print(json.dumps({
            "result": "PASS",
            "files_checked": len(py_files)
        }))
        sys.exit(0)
    else:
        print(json.dumps({
            "result": "FAIL",
            "violations": violations
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
