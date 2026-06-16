from __future__ import annotations

import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "datasets" / "gen"
DST = ROOT / "datasets" / "railway_obstacle_yolo"

CLASS_MAP = {
    "animals": (0, "animal"),
    "motos": (1, "motorcycle"),
    "persons": (2, "person"),
    "rocks": (3, "rock"),
    "vehicles": (4, "vehicle"),
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
TRAIN_RATIO = 0.9
SEED = 20260611


def parse_label_line(line: str, class_id: int) -> str | None:
    parts = line.strip().split()
    if len(parts) != 5:
        return None

    try:
        values = [float(v) for v in parts[1:]]
    except ValueError:
        return None

    if any(v < 0 or v > 1 for v in values):
        return None

    return f"{class_id} " + " ".join(f"{v:.10g}" for v in values)


def reset_output_dir() -> None:
    if DST.exists():
        shutil.rmtree(DST)

    for split in ("train", "val"):
        (DST / "images" / split).mkdir(parents=True, exist_ok=True)
        (DST / "labels" / split).mkdir(parents=True, exist_ok=True)


def collect_items() -> list[tuple[Path, Path, int, str]]:
    items: list[tuple[Path, Path, int, str]] = []
    skipped_missing_label = 0

    for folder, (class_id, _) in CLASS_MAP.items():
        img_dir = SRC / folder / "imgs"
        label_dir = SRC / folder / "anno"

        for image_path in sorted(img_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTS:
                continue

            label_path = label_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                skipped_missing_label += 1
                continue

            items.append((image_path, label_path, class_id, folder))

    if skipped_missing_label:
        print(f"Skipped images without labels: {skipped_missing_label}")

    return items


def write_data_yaml() -> None:
    names = [name for _, name in sorted(CLASS_MAP.values())]
    lines = [
        f"path: {DST.as_posix()}",
        "train: images/train",
        "val: images/val",
        "",
        "names:",
    ]
    lines.extend(f"  {idx}: {name}" for idx, name in enumerate(names))
    (DST / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    reset_output_dir()
    items = collect_items()
    random.Random(SEED).shuffle(items)

    split_index = int(len(items) * TRAIN_RATIO)
    split_items = {
        "train": items[:split_index],
        "val": items[split_index:],
    }

    invalid_labels = 0
    empty_labels = 0

    for split, entries in split_items.items():
        for image_path, label_path, class_id, folder in entries:
            out_stem = f"{folder}_{image_path.stem}"
            out_image = DST / "images" / split / f"{out_stem}{image_path.suffix.lower()}"
            out_label = DST / "labels" / split / f"{out_stem}.txt"

            shutil.copy2(image_path, out_image)

            converted_lines: list[str] = []
            for line in label_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                converted = parse_label_line(line, class_id)
                if converted is None:
                    invalid_labels += 1
                    continue
                converted_lines.append(converted)

            if not converted_lines:
                empty_labels += 1

            out_label.write_text("\n".join(converted_lines) + ("\n" if converted_lines else ""), encoding="utf-8")

    write_data_yaml()

    print(f"Created: {DST}")
    print(f"Total images: {len(items)}")
    print(f"Train images: {len(split_items['train'])}")
    print(f"Val images: {len(split_items['val'])}")
    print(f"Invalid label lines skipped: {invalid_labels}")
    print(f"Empty output labels: {empty_labels}")
    print("Classes:")
    for folder, (class_id, name) in CLASS_MAP.items():
        print(f"  {class_id}: {name} ({folder})")


if __name__ == "__main__":
    main()
