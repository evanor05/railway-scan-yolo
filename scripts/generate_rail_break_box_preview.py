from pathlib import Path
import argparse

from PIL import Image, ImageDraw, ImageFont


DEFAULT_IMAGE = Path(
    r"C:\Users\along\AppData\Local\Temp\codex-clipboard-4ff36a28-34bd-4ffa-8915-f116fdd40a0f.png"
)
DEFAULT_OUTPUT = Path(r"E:\yolov26\test_images\rail_break_labelimg_example.png")

# Recommended LabelImg-style box for the visible broken rail area in this image.
# Format: left, top, right, bottom.
DEFAULT_BOX = (95, 45, 230, 205)


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_box_preview(image_path: Path, output_path: Path, box: tuple[int, int, int, int]) -> None:
    image = Image.open(image_path).convert("RGB")
    annotated = image.copy()

    overlay = Image.new("RGBA", annotated.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    draw = ImageDraw.Draw(annotated)

    x1, y1, x2, y2 = box
    red = (255, 35, 35)

    overlay_draw.rectangle(box, fill=(255, 35, 35, 42))
    annotated = Image.alpha_composite(annotated.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(annotated)

    for offset in range(4):
        draw.rectangle((x1 - offset, y1 - offset, x2 + offset, y2 + offset), outline=red)

    handle = 6
    for hx, hy in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
        draw.rectangle(
            (hx - handle, hy - handle, hx + handle, hy + handle),
            fill=(255, 255, 255),
            outline=red,
            width=2,
        )

    font = load_font(15)
    label = "broken_rail"
    label_bbox = draw.textbbox((x1, y1), label, font=font)
    label_w = label_bbox[2] - label_bbox[0]
    label_h = label_bbox[3] - label_bbox[1]
    label_y = max(0, y1 - label_h - 9)
    draw.rectangle((x1, label_y, x1 + label_w + 10, label_y + label_h + 8), fill=red)
    draw.text((x1 + 5, label_y + 3), label, fill=(255, 255, 255), font=font)

    margin = 18
    gap = 20
    title_h = 36
    w, h = image.size
    canvas = Image.new("RGB", (w * 2 + gap + margin * 2, h + title_h + margin * 2), (245, 246, 248))
    canvas_draw = ImageDraw.Draw(canvas)
    title_font = load_font(17)
    small_font = load_font(13)

    left_xy = (margin, margin + title_h)
    right_xy = (margin + w + gap, margin + title_h)
    canvas.paste(image, left_xy)
    canvas.paste(annotated, right_xy)

    canvas_draw.text((left_xy[0], margin), "Original image", fill=(35, 35, 35), font=title_font)
    canvas_draw.text((right_xy[0], margin), "Recommended LabelImg box", fill=(35, 35, 35), font=title_font)

    note = f"box: x={x1}-{x2}, y={y1}-{y2}"
    canvas_draw.text((right_xy[0], right_xy[1] + h + 4), note, fill=(80, 80, 80), font=small_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Box must be four integers: left,top,right,bottom")
    return tuple(parts)  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a LabelImg-style rail-break box preview.")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="Input image path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output preview image path.")
    parser.add_argument("--box", type=parse_box, default=DEFAULT_BOX, help="left,top,right,bottom")
    args = parser.parse_args()

    draw_box_preview(args.image, args.output, args.box)
    print(args.output)


if __name__ == "__main__":
    main()
