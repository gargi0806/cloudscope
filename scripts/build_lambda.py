"""Build a self-contained Lambda zip with pinned SDK dependencies."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "dist" / "cloudscope-lambda.zip"
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cloudscope-") as directory:
        target = Path(directory)
        subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                        "--only-binary=:all:", "--no-compile", "--requirement", str(ROOT / "requirements.lock"),
                        "--target", str(target)], check=True)
        shutil.copytree(ROOT / "cloudscope", target / "cloudscope", ignore=shutil.ignore_patterns("__pycache__"))
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            for file in sorted(target.rglob("*")):
                if file.is_file() and "__pycache__" not in file.parts:
                    archive.write(file, file.relative_to(target))
    print(f"Built {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
