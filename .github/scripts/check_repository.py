# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML==6.0.3", "markdown-it-py==4.0.0", "mdurl==0.1.2"]
# ///
"""Repository CI: check skills, evaluation data, and local Markdown file links."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt


def load_validator(root):
    path = root / "skill/scripts/validate.py"
    spec = importlib.util.spec_from_file_location("skill_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def json_format_errors(path):
    try:
        text = path.read_text(encoding="utf-8")
        json.loads(text, object_pairs_hook=unique_object)
        errors = []
        if not text.endswith("\n"):
            errors.append("JSON file must end with a newline")
        if any(line != line.rstrip() for line in text.splitlines()):
            errors.append("JSON file contains trailing whitespace")
        return errors
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]


def evaluation_errors(path, skill):
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(data, dict) or data.get("skill_name") != skill.name:
            return ["skill_name must match the skill directory"]
        cases = data.get("evals")
        if not isinstance(cases, list) or not cases:
            return ["evals must be a nonempty array"]
        ids = set()
        for case in cases:
            if not isinstance(case, dict):
                errors.append("each eval must be an object")
                continue
            identifier = case.get("id")
            if type(identifier) is not int or identifier < 1 or identifier in ids:
                errors.append("eval IDs must be unique positive integers")
            else:
                ids.add(identifier)
            for field in ("prompt", "expected_output"):
                if not isinstance(case.get(field), str) or not case[field].strip():
                    errors.append(f"eval {identifier}: {field} must be a nonempty string")
            files = case.get("files", [])
            if not isinstance(files, list):
                errors.append(f"eval {identifier}: files must be an array")
                continue
            for name in files:
                if not isinstance(name, str):
                    errors.append(f"eval {identifier}: file paths must be strings")
                    continue
                target = (skill / name).resolve()
                if not target.is_relative_to(skill.resolve()) or not target.is_file():
                    errors.append(f"eval {identifier}: missing/escaping input file: {name}")
        queries = data.get("trigger_queries")
        if not isinstance(queries, list) or not queries:
            errors.append("trigger_queries must be a nonempty array")
        else:
            seen = set()
            for query in queries:
                if not isinstance(query, dict):
                    errors.append("each trigger query must be an object")
                    continue
                text = query.get("query")
                if not isinstance(text, str) or not text.strip():
                    errors.append("trigger query must be a nonempty string")
                elif text in seen:
                    errors.append(f"duplicate trigger query: {text}")
                else:
                    seen.add(text)
                if type(query.get("should_trigger")) is not bool:
                    errors.append("should_trigger must be a JSON boolean")
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def local_link_errors(path, root):
    """Parse actual Markdown links, including reference-style links, not examples."""
    errors = []
    parser = MarkdownIt()
    try:
        tokens = parser.parse(path.read_text(encoding="utf-8"))
        for token in tokens:
            for child in token.children or []:
                value = child.attrGet("href") if child.type == "link_open" else None
                if child.type == "image":
                    value = child.attrGet("src")
                if not value:
                    continue
                url = urlsplit(value)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (path.parent / unquote(url.path)).resolve()
                if not target.is_relative_to(root.resolve()):
                    errors.append(f"link leaves repository: {value}")
                elif not target.exists():
                    errors.append(f"missing local link: {value}")
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def check(root):
    root = root.resolve()
    errors = []
    skills = sorted(p.parent for p in root.glob("*/SKILL.md"))
    if not skills:
        return {"valid": False, "skills": 0, "errors": ["no root-level skills found"]}
    validator = load_validator(root)
    for skill in skills:
        result = validator.validate(skill)
        errors.extend(f"{skill.name}/SKILL.md: {error}" for error in result["errors"])
        path = skill / "evals/evals.json"
        errors.extend(f"{path.relative_to(root)}: {error}" for error in evaluation_errors(path, skill))
    for path in root.glob("*/evals/evals.json"):
        if path.parent.parent not in skills:
            errors.append(f"{path.relative_to(root)}: orphan evaluations without SKILL.md")
    json_files = set(root.glob("*.json")) | set(root.glob("*/evals/evals.json"))
    json_files.update((root / ".github/actions").glob("*/*.json"))
    for path in sorted(json_files):
        errors.extend(f"{path.relative_to(root)}: {error}" for error in json_format_errors(path))
    # Inspect maintained documentation, not dependencies, Git internals or build output.
    markdown = set(root.glob("*.md"))
    for directory in [root / "docs", root / ".github", *skills]:
        markdown.update(directory.rglob("*.md"))
    for path in sorted(markdown):
        errors.extend(f"{path.relative_to(root)}: {error}" for error in local_link_errors(path, root))
    return {"valid": not errors, "skills": len(skills), "errors": errors}


def main():
    parser = argparse.ArgumentParser(
        description="Read-only collection checks; JSON on stdout. Local paths only, no external URLs or fragment validation.",
        epilog="Exit 0: valid; 1: validation/input failure; 2: CLI misuse. Example: check_repository.py .",
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    try:
        result = check(args.root)
    except (OSError, ImportError, ValueError) as exc:
        result = {"valid": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
