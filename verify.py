"""Local release checks: outputs, tests, links and heuristic content scan."""
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs = set(), []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError("Duplicate HTML anchor")
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])

def check_links():
    page = ROOT / "reports/index.html"
    parser = Links()
    parser.feed(page.read_text(encoding="utf-8"))
    for href in parser.hrefs:
        parsed = urlparse(href)
        if parsed.scheme:
            continue
        if not parsed.path:
            if parsed.fragment not in parser.ids:
                raise ValueError("Missing anchor: " + href)
        elif not (page.parent / unquote(parsed.path)).is_file():
            raise ValueError("Missing local report link: " + href)
    return len(parser.hrefs)

def scan():
    # Heuristics only; emits filenames, never matching values.
    patterns = [
        r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"github_pat_[A-Za-z0-9_]{20,}",
        r"AKIA[A-Z0-9]{16}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        r"C:\\Users\\",
    ]
    files = [p for p in ROOT.rglob("*") if p.is_file()
             and not any(part in (".git", "__pycache__", ".venv") for part in p.relative_to(ROOT).parts)]
    hits = []
    for path in files:
        if path.suffix not in (".py", ".json", ".csv", ".md", ".html", "") and path.name != ".gitignore":
            continue
        text = path.read_text(encoding="utf-8")
        if any(re.search(pattern, text) for pattern in patterns):
            hits.append(path.relative_to(ROOT).as_posix())
    if hits:
        raise ValueError("Review possible personal-data/secret matches in: " + ", ".join(hits))
    return len(files)

def main():
    logs = []
    for command in ([sys.executable, "lab.py", "validate"],
                    [sys.executable, "lab.py", "build"],
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                    [sys.executable, "lab.py", "check"]):
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        label = "python " + " ".join(command[1:])
        logs.append("$ " + label + "\n" + result.stdout + result.stderr + f"exit_code={result.returncode}\n")
        if result.returncode:
            print(logs[-1])
            return result.returncode
    links = check_links()
    files = scan()
    logs.append(f"Local HTML links checked: {links}\nHeuristic content scan: {files} files; no matches.\n")
    (ROOT / "docs/verification-output.txt").write_text("\n".join(logs), encoding="utf-8")
    print(f"All release checks passed. HTML links: {links}; scanned files: {files}.")
    print("Five synthetic findings remain; these checks do not establish control effectiveness.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
