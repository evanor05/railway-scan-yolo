from __future__ import annotations

import argparse
from pathlib import Path

import cv2


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def check_split(root: Path, split: str, nc: int) -> tuple[int, int, list[str]]:
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    image_count = 0
    box_count = 0
    errors: list[str] = []

    for image_path in image_dir.rglob("*"):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        image_count += 1

        image = cv2.imread(str(image_path))
        if image is None:
            errors.append(f"unreadable image: {image_path}")
            continue

        rel = image_path.relative_to(image_dir)
        label_path = (label_dir / rel).with_suffix(".txt")
        if not label_path.exists():
            errors.append(f"missing label: {label_path}")
            continue

        for line_no, line in enumerate(label_path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != 5:
                errors.append(f"bad field count: {label_path}:{line_no}: {stripped}")
                continue
            try:
                cls = int(float(parts[0]))
                values = [float(v) for v in parts[1:]]
            except ValueError:
                errors.append(f"non-numeric label: {label_path}:{line_no}: {stripped}")
                continue
            if cls < 0 or cls >= nc:
                errors.append(f"class out of range: {label_path}:{line_no}: {stripped}")
            if any(v < 0 or v > 1 for v in values):
                errors.append(f"coordinate out of range: {label_path}:{line_no}: {stripped}")
            if values[2] <= 0 or values[3] <= 0:
                errors.append(f"non-positive box size: {label_path}:{line_no}: {stripped}")
            box_count += 1

    return image_count, box_count, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a YOLO detection dataset for unreadable images and bad labels.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--nc", type=int, default=5)
    parser.add_argument("--max-errors", type=int, default=50)
    args = parser.parse_args()

    root = args.root.resolve()
    all_errors: list[str] = []
    for split in ("train", "val"):
        images, boxes, errors = check_split(root, split, args.nc)
        all_errors.extend(errors)
        print(f"{split}: images={images} boxes={boxes} errors={len(errors)}")

    if all_errors:
        print("First errors:")
        for error in all_errors[: args.max_errors]:
            print(error)
        return 1

    print("Dataset integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
