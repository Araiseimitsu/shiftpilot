"""ブランド用 icon.ico を生成（PyInstaller / 将来の webview 用）。"""
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    root = Path(__file__).resolve().parent
    Path(root / "icon.ico").parent.mkdir(parents=True, exist_ok=True)
    w, h = 256, 256
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=(44, 74, 82, 255))
    bar_h = int(h * 0.18)
    gap = int(h * 0.065)
    marg = int(w * 0.13)
    total_h = bar_h * 3 + gap * 2
    y0 = (h - total_h) // 2
    colors = [(255, 255, 255, 255), (255, 255, 255, 230), (184, 221, 235, 255)]
    for i, c in enumerate(colors):
        y = y0 + i * (bar_h + gap)
        d.rounded_rectangle(
            [marg, y, w - marg, y + bar_h],
            radius=max(4, int(bar_h * 0.25)),
            fill=c,
        )
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    resized = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    out = root / "icon.ico"
    resized[0].save(out, format="ICO", append_images=resized[1:])
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
