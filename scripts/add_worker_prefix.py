from __future__ import annotations

from pathlib import Path


ROOT = Path(r"E:\yolov26\datasets\_process\worker_person")
PREFIX = "worker_"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABEL_EXTS = {".txt"}


def rename_files(base_dir: Path, allowed_exts: set[str]) -> tuple[int, int]:
    renamed = 0
    skipped = 0

    if not base_dir.exists():
        print(f"Missing directory: {base_dir}")
        return renamed, skipped

    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_exts:
            continue
        if path.name.startswith(PREFIX):
            skipped += 1
            continue

        target = path.with_name(f"{PREFIX}{path.name}")
        if target.exists():
            raise FileExistsError(f"Target already exists: {target}")

        path.rename(target)
        renamed += 1

    return renamed, skipped


def main() -> None:
    image_renamed, image_skipped = rename_files(ROOT / "images", IMAGE_EXTS)
    label_renamed, label_skipped = rename_files(ROOT / "labels", LABEL_EXTS)

    print(f"Images renamed: {image_renamed}")
    print(f"Images already prefixed: {image_skipped}")
    print(f"Labels renamed: {label_renamed}")
    print(f"Labels already prefixed: {label_skipped}")
    print("Done.")


if __name__ == "__main__":
    main()
