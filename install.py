#!/usr/bin/env python3
"""
One-click installer for the news-agent project.
Run: python3 install.py
"""

import base64
import os
import subprocess
import sys

INSTALL_DIR = os.path.expanduser("~/Desktop/news-agent")

# All project files encoded as base64 to avoid shell escaping issues
FILES = {}


def encode_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def main():
    # This script is meant to be run from the Claude Code session
    # to generate the actual installer. See generate() below.
    print("This script should be generated first. Run generate() to produce the installer.")


def generate():
    """Read all project files and print a self-contained installer script."""
    project_dir = os.path.dirname(os.path.abspath(__file__))

    files_to_include = [
        ".gitignore",
        ".env",
        ".env.example",
        ".github/workflows/weekly-news.yml",
        "analyze.py",
        "config.py",
        "main.py",
        "notion_client.py",
        "requirements.txt",
        "search.py",
    ]

    encoded = {}
    for f in files_to_include:
        filepath = os.path.join(project_dir, f)
        if os.path.exists(filepath):
            encoded[f] = encode_file(filepath)

    # Print the self-contained installer
    print("#!/usr/bin/env python3")
    print('"""Auto-generated installer for news-agent."""')
    print("import base64, os, subprocess, sys")
    print()
    print(f"INSTALL_DIR = os.path.expanduser('~/Desktop/news-agent')")
    print()
    print("FILES = {")
    for name, data in encoded.items():
        print(f"    {name!r}: {data!r},")
    print("}")
    print()
    print("""
def main():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    for relpath, data in FILES.items():
        fullpath = os.path.join(INSTALL_DIR, relpath)
        os.makedirs(os.path.dirname(fullpath), exist_ok=True)
        with open(fullpath, 'wb') as f:
            f.write(base64.b64decode(data))
        print(f"  Created {relpath}")

    print(f"\\nAll files written to {INSTALL_DIR}")
    print("\\nNext steps:")
    print("  cd ~/Desktop/news-agent")
    print("  ./setup.sh")

if __name__ == "__main__":
    main()
""")


if __name__ == "__main__":
    generate()
