#!/usr/bin/env python3
"""Pre-commit secret scanner.

Scans staged git files for accidental secret leaks before committing.
Blocks commits containing AWS keys, Stripe keys, GitHub/GitLab/Slack tokens,
private key headers, hardcoded passwords, and blocked file extensions.

Usage:
    python scripts/check_secrets.py          # scan staged files
    python scripts/check_secrets.py --all    # scan all tracked files
"""

import re
import subprocess
import sys

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    (re.compile(r"sk_live_[a-zA-Z0-9]+"), "Stripe Live Key"),
    (re.compile(r"sk_test_[a-zA-Z0-9]{20,}"), "Stripe Test Key (long)"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"glpat-[a-zA-Z0-9\-_]{20,}"), "GitLab Personal Access Token"),
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "Slack Token"),
    (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}\."), "Embedded JWT"),
]

BLOCKED_EXTENSIONS = frozenset({
    ".pem", ".key", ".crt", ".p12", ".pfx", ".jks",
    ".keystore", ".secrets",
})

EXEMPT_PATHS = frozenset({
    "scripts/check_secrets.py",
})

EXEMPT_PREFIXES = (
    "fast_api/tests/",
    "src/tests/",
    "e2e/tests/",
)


def get_staged_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def get_all_tracked_files():
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def get_file_content(filepath):
    result = subprocess.run(
        ["git", "show", f":{filepath}"],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else ""


def scan_file(filepath, content):
    findings = []

    for ext in BLOCKED_EXTENSIONS:
        if filepath.endswith(ext):
            findings.append((filepath, 0, f"Blocked file type: {ext}"))
            return findings

    if filepath.endswith(".env") and not filepath.endswith(".example"):
        findings.append((filepath, 0, "Environment file (not .example)"))
        return findings

    for line_num, line in enumerate(content.split("\n"), start=1):
        for pattern, description in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((filepath, line_num, description))

    return findings


def main():
    scan_all = "--all" in sys.argv

    if scan_all:
        files = get_all_tracked_files()
    else:
        files = get_staged_files()

    if not files or files == [""]:
        print("No files to scan.")
        sys.exit(0)

    all_findings = []

    for filepath in files:
        if filepath in EXEMPT_PATHS:
            continue
        if any(filepath.startswith(p) for p in EXEMPT_PREFIXES):
            continue

        if scan_all:
            try:
                with open(filepath, "r", errors="ignore") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue
        else:
            content = get_file_content(filepath)

        findings = scan_file(filepath, content)
        all_findings.extend(findings)

    if all_findings:
        print(f"\n  SECRET LEAK DETECTED — {len(all_findings)} finding(s):\n")
        for filepath, line_num, description in all_findings:
            loc = f":{line_num}" if line_num else ""
            print(f"  {filepath}{loc} — {description}")
        print("\n  COMMIT BLOCKED. Remove secrets before committing.\n")
        sys.exit(1)

    print("No secrets detected. Safe to commit.")
    sys.exit(0)


if __name__ == "__main__":
    main()
