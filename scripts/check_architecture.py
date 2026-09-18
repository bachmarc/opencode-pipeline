#!/usr/bin/env python3
"""Check architecture rules for src/core/ modules (polyglot).

Checks import statements per language, detected by file suffix, in the given
directory (recursively):

- ``.py`` — Python AST path (unchanged behavior); imports checked against the
  Python stdlib allowlist (deterministic set, see ``get_stdlib_modules``).
- ``.js``/``.ts``/``.jsx``/``.tsx`` — regex-based extraction of bare-specifier
  imports from ``import ... from 'mod'``, side-effect ``import 'mod'``,
  ``require('mod')``, dynamic ``import('mod')`` and re-exports
  (``export ... from 'mod'``). Relative specifiers (``./``, ``../``) are
  project-internal and ALWAYS allowed (core may call core). Non-relative
  specifiers are checked against the Node-builtin allowlist.
- ``.rb`` — regex-based ``require 'x'`` / ``require "x"`` checked against a
  Ruby-stdlib set. ``require_relative`` is project-internal and is never
  matched (different keyword) → ALWAYS allowed.
- ``.java`` — regex-based ``import [static] <pkg>.<Class>;``; allowed
  prefixes ``java.``, ``javax.``, ``jakarta.`` (platform); everything else
  (e.g. third-party frameworks) is forbidden unless allowlisted.

Custom allowlist (``--allowlist`` file, one module/package per line) is
unioned with each language's default allowlist and works for ALL languages.

Simplification: regex-based extraction does NOT validate syntax — it only
finds import statements (unreadable files are skipped, as with Python today).

Violation JSON format (unchanged): ``{"file", "import", "line"}`` — no new
fields. PASS output: ``{"result": "PASS", "files_checked": <N>}`` where N
counts all checked files across languages; the FAIL output carries the same
``files_checked`` count so mixed-language runs stay auditable.

Exit codes:
  0 - PASS: all imports are allowed
  1 - FAIL: forbidden imports found
"""

import ast
import json
import re
import sys
import sysconfig
from pathlib import Path
from typing import Dict, List, Set, Tuple

PYTHON_SUFFIX = ".py"
RUBY_SUFFIX = ".rb"
JAVA_SUFFIX = ".java"
JS_SUFFIXES = frozenset({".js", ".ts", ".jsx", ".tsx"})

# All file patterns checked in one run (rglob over src/core/).
CHECKED_GLOBS = (
    "*.py",
    "*.js",
    "*.ts",
    "*.jsx",
    "*.tsx",
    "*.rb",
    "*.java",
)

# Node.js built-in modules: allowed for JS/TS core code.
NODE_BUILTINS = frozenset({
    "assert", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "dns", "domain", "events", "fs", "http", "http2",
    "https", "inspector", "module", "net", "os", "path", "perf_hooks",
    "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "timers", "tls", "tty", "url", "util", "v8", "vm",
    "worker_threads", "zlib",
})

# Ruby stdlib (top-level requires): allowed for Ruby core code.
RUBY_STDLIB = frozenset({
    "base64", "benchmark", "bigdecimal", "cgi", "coverage", "csv", "date",
    "dbm", "digest", "erb", "etc", "fileutils", "find", "forwardable",
    "getoptlong", "ipaddr", "json", "logger", "monitor", "mutex_m",
    "net/ftp", "net/http", "net/imap", "net/pop", "net/smtp", "nkf",
    "objspace", "observer", "open-uri", "open3", "openssl", "optparse",
    "ostruct", "pathname", "pp", "prettyprint", "pstore", "psych", "rdoc",
    "resolv", "resolv-replace", "ripper", "scanf", "securerandom", "set",
    "shellwords", "singleton", "socket", "stringio", "stringscan", "syslog",
    "tempfile", "thread", "time", "timeout", "tmpdir", "tsort", "uri",
    "weakref", "win32ole", "yaml", "zlib",
})

# Java platform prefixes: allowed for Java core code.
JAVA_ALLOWED_PREFIXES = ("java.", "javax.", "jakarta.")


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


def extract_python_imports(file_path: Path) -> List[Tuple[str, int]]:
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


_JS_IMPORT_RE = re.compile(
    r"(?:from\s+|require\(\s*|import\(\s*|import\s+)['\"]([^'\"]+)['\"]"
)


def extract_js_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Extract bare-specifier imports from a JS/TS file via regex.

    Matches ``import ... from 'mod'``, side-effect ``import 'mod'``,
    ``require('mod')``, dynamic ``import('mod')`` and re-exports
    (``export ... from 'mod'``). Relative specifiers (``./``, ``../``) are
    project-internal and skipped (always allowed: core may call core).

    Regex extraction does NOT validate syntax. Returns list of
    (module, line_number) tuples.
    """
    imports: List[Tuple[str, int]] = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        # Skip files that can't be read
        return imports
    
    seen: Set[Tuple[str, int]] = set()
    for match in _JS_IMPORT_RE.finditer(content):
        specifier = match.group(1)
        if specifier.startswith('./') or specifier.startswith('../'):
            # Project-internal relative import -> always allowed
            continue
        line_no = content.count('\n', 0, match.start()) + 1
        if (specifier, line_no) in seen:
            continue
        seen.add((specifier, line_no))
        imports.append((specifier, line_no))
    return imports


_RUBY_REQUIRE_RE = re.compile(
    r"^\s*require\s+['\"]([^'\"]+)['\"]", re.MULTILINE
)


def extract_ruby_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Extract ``require 'x'`` targets from a Ruby file via regex.

    ``require_relative`` is never matched (different keyword) — it is
    project-internal and always allowed.

    Regex extraction does NOT validate syntax. Returns list of
    (module, line_number) tuples.
    """
    imports: List[Tuple[str, int]] = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        # Skip files that can't be read
        return imports
    
    seen: Set[Tuple[str, int]] = set()
    for match in _RUBY_REQUIRE_RE.finditer(content):
        module = match.group(1)
        line_no = content.count('\n', 0, match.start()) + 1
        if (module, line_no) in seen:
            continue
        seen.add((module, line_no))
        imports.append((module, line_no))
    return imports


_JAVA_IMPORT_RE = re.compile(
    r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;", re.MULTILINE
)


def extract_java_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Extract ``import [static] <pkg>.<Class>;`` packages via regex.

    Regex extraction does NOT validate syntax. Returns list of
    (package, line_number) tuples.
    """
    imports: List[Tuple[str, int]] = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        # Skip files that can't be read
        return imports
    
    seen: Set[Tuple[str, int]] = set()
    for match in _JAVA_IMPORT_RE.finditer(content):
        package = match.group(1)
        line_no = content.count('\n', 0, match.start()) + 1
        if (package, line_no) in seen:
            continue
        seen.add((package, line_no))
        imports.append((package, line_no))
    return imports


def extract_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Extract import statements from a file, dispatched on its suffix.

    ``.py`` -> Python AST extraction (unchanged);
    ``.js``/``.ts``/``.jsx``/``.tsx`` -> JS regex extraction;
    ``.rb`` -> Ruby regex extraction; ``.java`` -> Java regex extraction;
    other suffixes -> ``[]``.
    """
    suffix = file_path.suffix.lower()
    if suffix == PYTHON_SUFFIX:
        return extract_python_imports(file_path)
    if suffix in JS_SUFFIXES:
        return extract_js_imports(file_path)
    if suffix == RUBY_SUFFIX:
        return extract_ruby_imports(file_path)
    if suffix == JAVA_SUFFIX:
        return extract_java_imports(file_path)
    return []


def java_import_allowed(package: str, custom_allowlist: Set[str]) -> bool:
    """Check a Java package against platform prefixes and the custom allowlist.

    Platform prefixes (``java.``, ``javax.``, ``jakarta.``) match the first
    package segment; a custom allowlist entry matches the full package
    exactly or as a package prefix (entry + ``.``).
    """
    if package.startswith(JAVA_ALLOWED_PREFIXES):
        return True
    for entry in custom_allowlist:
        if package == entry or package.startswith(entry + '.'):
            return True
    return False


def check_architecture(
    src_core_path: Path, custom_allowlist: Set[str]
) -> Tuple[bool, List[Dict], int]:
    """Check all source files in src/core/ for forbidden imports.

    rglob over ``*.py``, ``*.js``, ``*.ts``, ``*.jsx``, ``*.tsx``, ``*.rb``,
    ``*.java``; each language is checked against its default allowlist
    unioned with the custom allowlist (Python keeps the existing
    stdlib+custom semantics byte-identically).

    Returns (is_clean, list_of_violations, files_checked).
    """
    violations: List[Dict] = []
    
    if not src_core_path.exists():
        return False, [{"error": f"Path not found: {src_core_path}"}], 0
    
    files = [
        file
        for pattern in CHECKED_GLOBS
        for file in src_core_path.rglob(pattern)
        if file.is_file()
    ]
    
    python_allowed = get_stdlib_modules() | custom_allowlist
    js_allowed = set(NODE_BUILTINS) | custom_allowlist
    ruby_allowed = set(RUBY_STDLIB) | custom_allowlist
    
    for file in files:
        suffix = file.suffix.lower()
        imports = extract_imports(file)
        
        for module_name, line_no in imports:
            if suffix in JS_SUFFIXES:
                forbidden = module_name not in js_allowed
            elif suffix == RUBY_SUFFIX:
                forbidden = module_name not in ruby_allowed
            elif suffix == JAVA_SUFFIX:
                forbidden = not java_import_allowed(module_name, custom_allowlist)
            else:  # .py (globs guarantee a known suffix)
                forbidden = module_name not in python_allowed
            
            if forbidden:
                violations.append({
                    "file": str(file.relative_to(src_core_path.parent)),
                    "import": module_name,
                    "line": line_no
                })
    
    files_checked = len(files)
    is_clean = len(violations) == 0
    return is_clean, violations, files_checked


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "result": "FAIL",
            "error": "Usage: check_architecture.py <src-core-path> [--allowlist <file>]"
        }))
        sys.exit(1)
    
    src_core_path = Path(sys.argv[1])
    
    # Custom allowlist for all languages (empty by default)
    custom_allowlist: Set[str] = set()
    
    # Check for custom allowlist
    if len(sys.argv) >= 4 and sys.argv[2] == "--allowlist":
        allowlist_file = Path(sys.argv[3])
        custom_allowlist = load_allowlist(allowlist_file)
    
    # Check architecture
    is_clean, violations, files_checked = check_architecture(
        src_core_path, custom_allowlist
    )
    
    if is_clean:
        print(json.dumps({
            "result": "PASS",
            "files_checked": files_checked
        }))
        sys.exit(0)
    else:
        print(json.dumps({
            "result": "FAIL",
            "violations": violations,
            "files_checked": files_checked
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()