# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Read-only Agent Skills format and local Markdown-link checks."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys rather than silently overwriting them."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def validate(directory):
    directory = Path(directory).resolve()
    errors, warnings = [], []
    path = directory / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)(.*)\Z", text, re.S)
        if not match:
            raise ValueError("expected opening/closing --- YAML frontmatter delimiters")
        data = yaml.load(match[1], Loader=UniqueLoader)
        if not isinstance(data, dict):
            raise ValueError("frontmatter must be a YAML mapping")
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        return {"path": str(directory), "errors": [str(exc)], "warnings": []}

    name = data.get("name")
    # The specification permits lowercase Unicode letters; ASCII is recommended
    # by this repository for broad client compatibility, not enforced as universal.
    if (not isinstance(name, str) or not 1 <= len(name) <= 64
            or name.startswith("-") or name.endswith("-") or "--" in name
            or any(not (c == "-" or c.isdigit() or (c.isalpha() and c.islower())) for c in name)):
        errors.append("name must be 1–64 lowercase alphanumeric/hyphen characters, without edge/double hyphens")
    if name != directory.name:
        errors.append("name must match the containing directory")
    for field, maximum in (("description", 1024), ("compatibility", 500)):
        value = data.get(field)
        if field == "compatibility" and field not in data:
            continue
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            errors.append(f"{field} must be a nonempty string of at most {maximum} characters")
    for field in ("license", "allowed-tools"):
        if field in data and not isinstance(data[field], str):
            errors.append(f"{field} must be a string")
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
        errors.append("metadata must map strings to strings")
    unknown = set(data) - FIELDS
    if unknown:
        errors.append(f"unknown fields (use metadata): {', '.join(sorted(unknown))}")
    if not match[2].strip():
        errors.append("Markdown instruction body is empty")
    if len(text.splitlines()) >= 500:
        warnings.append("SKILL.md should stay below 500 lines")

    # Explicit inline Markdown links only; not external URLs, anchors, reference
    # links, or literal example paths in code fences. This is not a full MD parser.
    for doc in sorted(directory.rglob("*.md")):
        try:
            content = doc.read_text(encoding="utf-8")
            content = re.sub(r"(?ms)^(`{3,}|~{3,}).*?^\1[^\n]*$", "", content)
            for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", content):
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (doc.parent / unquote(parsed.path)).resolve()
                if not target.is_relative_to(directory):
                    errors.append(f"{doc.relative_to(directory)}: link leaves skill directory: {link}")
                elif not target.exists():
                    errors.append(f"{doc.relative_to(directory)}: missing local link: {link}")
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{doc}: {exc}")
    return {"path": str(directory), "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(
        description="Read-only skill/frontmatter and local inline Markdown-link validation; JSON on stdout.",
        epilog="Examples: validate.py ./helm; validate.py --collection .\nExit: 0 valid, 1 validation failure, 2 CLI misuse. No external URL or behavior checks.")
    parser.add_argument("path", type=Path, help="skill directory, or collection root with --collection")
    parser.add_argument("--collection", action="store_true", help="check immediate child directories containing SKILL.md")
    args = parser.parse_args()
    directories = sorted(p.parent for p in args.path.glob("*/SKILL.md")) if args.collection else [args.path]
    results = [validate(p) for p in directories]
    if not results:
        results = [{"path": str(args.path), "errors": ["no immediate child SKILL.md files found"], "warnings": []}]
    valid = all(not result["errors"] for result in results)
    json.dump({"valid": valid, "skills": results}, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
