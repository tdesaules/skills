"""Build, exercise, and archive dedicated actions on the current native platform."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]


def capture(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def source_files():
    names = capture("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({name for name in names if name and (ROOT / name).is_file()})


def fingerprint(files):
    digest = hashlib.sha256()
    for name in files:
        path = ROOT / name
        digest.update(name.encode() + b"\0")
        content = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def execute(args, expected_code=0):
    print("+ " + " ".join(map(str, args)), file=sys.stderr)
    result = subprocess.run(list(map(str, args)), cwd=ROOT, stdout=sys.stderr, check=False)
    if result.returncode != expected_code:
        raise RuntimeError(f"Unexpected exit {result.returncode}: {args[0]}")


def run_image(image, workspace):
    return [
        "podman", "run", "--rm", "--network=none", "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,nodev", "--userns=keep-id:uid=65532,gid=65532",
        "-v", f"{workspace}:/github/workspace:ro,z", "-w", "/github/workspace", image,
    ]


def broken_fixture(name, destination, files):
    for relative in files:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, target)
    if name == "check":
        (destination / "skill/evals/evals.json").write_text('{"invalid":', encoding="utf-8")
    elif name == "lint-python":
        (destination / "undefined_ci_name.py").write_text("print(undefined_ci_name)\n", encoding="utf-8")
    elif name == "lint-markdown":
        (destination / "ci-negative.md").write_text("# Invalid layout\n\nTrailing space \n", encoding="utf-8")
    elif name == "lint-workflow":
        (destination / ".github/workflows/main.yml").write_text("name: invalid\non: push\njobs: {}\n", encoding="utf-8")
    elif name == "test-python":
        (destination / "tests/unit/test_ci_negative.py").write_text(
            "import unittest\nclass Negative(unittest.TestCase):\n"
            "    def test_failure(self):\n        self.fail('intentional qualification failure')\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(f"No negative qualification fixture for {name}")


def qualify(output):
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("--output must be outside the repository (contains archives and disposable fixtures)")
    output.mkdir(parents=True, exist_ok=True)
    arch = capture("podman", "info", "--format", "{{.Host.Arch}}")
    if arch not in ("amd64", "arm64"):
        raise ValueError(f"Unsupported native platform: {arch}")
    target = output / f"qualification-{arch}.json"
    # Never leave an earlier success receipt looking like this failed attempt.
    target.unlink(missing_ok=True)
    files = source_files()
    source_hash = fingerprint(files)
    revision = capture("git", "rev-parse", "HEAD")
    dirty = bool(capture("git", "status", "--porcelain"))
    receipts = []
    for recipe in sorted((ROOT / ".github/actions").glob("*/Containerfile")):
        name = recipe.parent.name
        iidfile = output / f"{name}-{arch}.id"
        execute(["podman", "build", "--iidfile", iidfile, "-f", recipe, recipe.parent])
        image = iidfile.read_text().strip()
        execute(run_image(image, ROOT))
        # Also exercise the image's own writable /tmp, without a tmpfs masking a
        # missing directory, and its numeric USER without keep-id compensation.
        execute([
            "podman", "run", "--rm", "--network=none", "-e", "HOME=/github/home",
            "-v", f"{ROOT}:/github/workspace:ro,z", "-w", "/github/workspace", image,
        ])
        with tempfile.TemporaryDirectory(prefix=f"{name}-negative-", dir=output) as temporary:
            fixture = Path(temporary)
            # keep-id maps the executing user's UID; the fixture remains private.
            broken_fixture(name, fixture, files)
            execute(run_image(image, fixture), expected_code=1)
        archive = output / f"{name}-{arch}.oci.tar"
        execute(["podman", "save", "--format", "oci-archive", "-o", archive, image])
        with archive.open("rb") as stream:
            checksum = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(chunk)
        receipts.append({
            "component": name, "arch": arch, "source_sha": revision,
            "source_fingerprint": source_hash, "source_dirty": dirty,
            "image_id": image, "archive": archive.name, "sha256": checksum.hexdigest(),
            "tested": True, "tests": [
                "read-only offline success", "numeric UID and image-provided temporary directory",
                "intentional invalid input fails",
            ],
        })
    if not receipts:
        raise ValueError("No action Containerfiles found")
    if source_hash != fingerprint(source_files()):
        raise ValueError("Source changed during qualification; discard these candidates and rerun")
    result = {"schema_version": 1, "platform": f"linux/{arch}", "receipts": receipts}
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"report": str(target), "images": len(receipts), "source_dirty": dirty}


def main():
    parser = argparse.ArgumentParser(
        description="Build/test native OCI action images with rootless Podman; archive exact tested images.",
        epilog="Requires Podman, Git and network during build. No push/login. Exit 0 passed, 1 failed, 2 invalid CLI. Example: --output /tmp/skills-ci",
    )
    parser.add_argument("--output", required=True, type=Path, help="external output directory for archives and qualification receipts")
    args = parser.parse_args()
    try:
        print(json.dumps(qualify(args.output), indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Qualification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
