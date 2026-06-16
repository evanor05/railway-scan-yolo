from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABEL_ROOT = ROOT / "datasets" / "_process" / "person" / "labels"
DEFAULT_BACKUP_ROOT = ROOT / "datasets" / "_process" / "person" / "labels_backup_class0_before_remap"


def iter_label_files(label_root: Path) -> list[Path]:
    files: list[Path] = []
    for split in ("train", "val", "test"):
        split_dir = label_root / split
        if split_dir.exists():
            files.extend(sorted(split_dir.glob("*.txt")))
    return files


def backup_labels(label_root: Path, backup_root: Path) -> None:
    if backup_root.exists():
        return

    for label_file in iter_label_files(label_root):
        relative = label_file.relative_to(label_root)
        out_file = backup_root / relative
        out_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(label_file, out_file)

    stamp_file = backup_root / "BACKUP_CREATED.txt"
    stamp_file.write_text(
        f"Backup created before remapping class 0 to 2.\n"
        f"Created at: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Source: {label_root}\n",
        encoding="utf-8",
    )


def remap_file(label_file: Path, src_class: str, dst_class: str) -> tuple[int, int, int]:
    changed = 0
    already_dst = 0
    other = 0
    output_lines: list[str] = []

    for raw_line in label_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            output_lines.append(raw_line)
            continue

        parts = stripped.split()
        if parts[0] == src_class:
            parts[0] = dst_class
            changed += 1
            output_lines.append(" ".join(parts))
        elif parts[0] == dst_class:
            already_dst += 1
            output_lines.append(" ".join(parts))
        else:
            other += 1
            output_lines.append(" ".join(parts))

    label_file.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    return changed, already_dst, other


def remove_yolo_caches(label_root: Path) -> int:
    removed = 0
    for cache_file in label_root.rglob("*.cache"):
        cache_file.unlink()
        removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remap YOLO person labels from class 0 to class 2 for obstacle dataset merging."
    )
    parser.add_argument("--label-root", type=Path, default=DEFAULT_LABEL_ROOT)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument("--src-class", default="0")
    parser.add_argument("--dst-class", default="2")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    label_root = args.label_root.resolve()
    backup_root = args.backup_root.resolve()

    if not label_root.exists():
        raise FileNotFoundError(f"Label root not found: {label_root}")

    label_files = iter_label_files(label_root)
    if not label_files:
        raise RuntimeError(f"No label txt files found under: {label_root}")

    if not args.no_backup:
        backup_labels(label_root, backup_root)

    total_changed = 0
    total_already_dst = 0
    total_other = 0
    touched_files = 0

    for label_file in label_files:
        changed, already_dst, other = remap_file(label_file, args.src_class, args.dst_class)
        total_changed += changed
        total_already_dst += already_dst
        total_other += other
        if changed:
            touched_files += 1

    removed_caches = remove_yolo_caches(label_root)

    print(f"Label root: {label_root}")
    print(f"Backup root: {backup_root if not args.no_backup else 'disabled'}")
    print(f"Label files scanned: {len(label_files)}")
    print(f"Files changed: {touched_files}")
    print(f"Boxes remapped {args.src_class} -> {args.dst_class}: {total_changed}")
    print(f"Boxes already {args.dst_class}: {total_already_dst}")
    print(f"Boxes with other class ids: {total_other}")
    print(f"YOLO cache files removed: {removed_caches}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
