from __future__ import annotations

import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OBSTACLE_ROOT = ROOT / "datasets" / "railway_obstacle_yolo"
PERSON_ROOT = ROOT / "datasets" / "_process" / "person"
OUT_ROOT = ROOT / "datasets" / "railway_obstacle_person_yolo"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "val")
DATASETS = (
    ("obstacle", OBSTACLE_ROOT),
    ("person", PERSON_ROOT),
)


def ensure_clean_output() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)

    for split in SPLITS:
        for kind in ("images", "labels"):
            for ds_name, _ in DATASETS:
                (OUT_ROOT / kind / split / ds_name).mkdir(parents=True, exist_ok=True)


def link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def merge_dataset(ds_name: str, src_root: Path) -> tuple[int, int]:
    image_count = 0
    label_count = 0

    for split in SPLITS:
        src_img_dir = src_root / "images" / split
        src_lab_dir = src_root / "labels" / split
        if not src_img_dir.exists() or not src_lab_dir.exists():
            raise FileNotFoundError(f"Missing split in {src_root}: {split}")

        out_img_dir = OUT_ROOT / "images" / split / ds_name
        out_lab_dir = OUT_ROOT / "labels" / split / ds_name

        for image_path in sorted(src_img_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTS:
                continue
            label_path = src_lab_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                raise FileNotFoundError(f"Missing label for {image_path}")

            link_or_copy(image_path, out_img_dir / image_path.name)
            link_or_copy(label_path, out_lab_dir / label_path.name)
            image_count += 1
            label_count += 1

    return image_count, label_count


def write_data_yaml() -> None:
    content = f"""path: {OUT_ROOT.as_posix()}
train: images/train
val: images/val

names:
  0: animal
  1: motorcycle
  2: person
  3: rock
  4: vehicle
"""
    (OUT_ROOT / "data.yaml").write_text(content, encoding="utf-8")


def summarize() -> None:
    for split in SPLITS:
        counts: dict[str, int] = {}
        images = 0
        labels = 0
        boxes = 0
        empty = 0

        for ds_name, _ in DATASETS:
            img_dir = OUT_ROOT / "images" / split / ds_name
            lab_dir = OUT_ROOT / "labels" / split / ds_name
            for image_file in sorted(img_dir.iterdir()):
                if image_file.suffix.lower() not in IMAGE_EXTS:
                    continue
                images += 1
                label_file = lab_dir / f"{image_file.stem}.txt"
                if not label_file.exists():
                    raise FileNotFoundError(f"Missing merged label: {label_file}")
                labels += 1
                had_box = False
                for line in label_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    parts = line.strip().split()
                    if not parts:
                        continue
                    had_box = True
                    counts[parts[0]] = counts.get(parts[0], 0) + 1
                    boxes += 1
                if not had_box:
                    empty += 1

        ordered = dict(sorted(counts.items(), key=lambda item: int(item[0])))
        print(f"{split}: images={images} labels={labels} boxes={boxes} empty_labels={empty} classes={ordered}")


def main() -> int:
    ensure_clean_output()
    totals = []
    for ds_name, src_root in DATASETS:
        totals.append((ds_name, *merge_dataset(ds_name, src_root)))

    write_data_yaml()

    print(f"Created: {OUT_ROOT}")
    for ds_name, images, labels in [(n, i, l) for n, i, l in [(t[0], t[1], t[2]) for t in totals]]:
        print(f"{ds_name}: images={images} labels={labels}")
    summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
