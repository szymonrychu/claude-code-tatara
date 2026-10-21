"""Component scaffold files."""

import json
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

LANGS: dict[str, dict] = {
    "python": {
        "tools": {"python": "3.14.6", "uv": "0.12.23", "ruff": "0.15.20", "pipx:pytest": "9.1.1"},
        "test": "pytest",
        "lint": "ruff check .",
        "fmt": "ruff format .",
    },
    "go": {
        "tools": {"go": "1.26.0", "golangci-lint": "2.5.0"},
        "test": "go test ./...",
        "lint": "golangci-lint run",
        "fmt": "gofmt -w .",
    },
    "typescript": {
        "tools": {"node": "24.20.0"},
        "test": "npm test",
        "lint": "npm run lint",
        "fmt": "npm run fmt",
    },
    "generic": {
        "tools": {},
        "test": "echo 'no tests defined yet' && exit 1",
        "lint": "echo 'no lint defined yet' && exit 1",
        "fmt": "echo 'no formatter defined yet'",
    },
}

GITIGNORE = {
    "python": ".venv/\n__pycache__/\n*.pyc\n.pytest_cache/\n.ruff_cache/\n",
    "go": "bin/\n*.test\n",
    "typescript": "node_modules/\ndist/\n",
    "generic": "",
}


def parse_component(spec: str) -> tuple[str, str]:
    name, _, lang = spec.partition(":")
    return name, lang or "generic"


def mise_toml(lang: str) -> str:
    cfg = LANGS[lang]
    out = ["[tools]"] if cfg["tools"] else []
    out += [f'"{k}" = "{v}"' if ":" in k else f'{k} = "{v}"' for k, v in cfg["tools"].items()]
    for task in ("test", "lint", "fmt"):
        out += [
            "",
            f"[tasks.{task}]",
            f'description = "Run {task}"',
            f"run = {json.dumps(cfg[task])}",
        ]
    return "\n".join(out) + "\n"


def starter_files(name: str, lang: str) -> dict[str, str]:
    """Files that make the component's own test task trivially green offline."""
    pkg = name.replace("-", "_")
    if lang == "python":
        return {"tests/test_smoke.py": "def test_smoke():\n    assert True\n"}
    if lang == "go":
        return {
            "go.mod": f"module {name}\n\ngo 1.26\n",
            "smoke.go": (
                f"package {pkg}\n\n// Smoke is a placeholder so the package builds.\n"
                "func Smoke() bool { return true }\n"
            ),
            "smoke_test.go": (
                f'package {pkg}\n\nimport "testing"\n\n'
                'func TestSmoke(t *testing.T) {\n\tif !Smoke() {\n\t\tt.Fatal("smoke")\n\t}\n}\n'
            ),
        }
    if lang == "typescript":
        scripts = {"test": "node --test", "lint": "node --check index.js", "fmt": "echo ok"}
        return {
            "package.json": json.dumps(
                {"name": name, "private": True, "scripts": scripts}, indent=2
            )
            + "\n",
            "index.js": "module.exports = { smoke: () => true };\n",
            "index.test.js": (
                "const test = require('node:test');\nconst assert = require('node:assert');\n"
                "test('smoke', () => assert.ok(require('./index').smoke()));\n"
            ),
        }
    return {}


def write(path: Path, project: str, name: str, lang: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    files = {
        "AGENTS.md": (
            f"# {name}\n\nComponent `{name}` ({lang}) of the {project} project. "
            "Its own tests, `MEMORY.md` and `ROADMAP.md` live here.\n\n"
            "Run `mise run test`, `mise run lint` and `mise run fmt` from this directory.\n"
        ),
        "CLAUDE.md": "@AGENTS.md\n",
        "MEMORY.md": f"# {name} memory\n\nLessons that outlive a session. Newest first.\n",
        "ROADMAP.md": f"# {name} roadmap\n\nHuman-owned requirements.\n",
        ".mise.toml": mise_toml(lang),
        ".gitignore": GITIGNORE[lang],
        "README.md": f"# {name}\n\nPart of the {project} project ({lang}).\n",
    }
    files.update(starter_files(name, lang))
    for rel, text in files.items():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        (path / rel).write_text(text)
