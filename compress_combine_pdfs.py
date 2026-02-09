"""
compress_combine_pdfs.py

Compresses and combines Civil3D sheet set PDFs into a single optimized file.
Uses Ghostscript to aggressively downsample raster content (heat ramps/elevation banding)
while preserving vector linework and text quality.

Usage:
    python compress_combine_pdfs.py input_folder/ output.pdf
    python compress_combine_pdfs.py input_folder/ output.pdf --dpi 200 --quality printer
    python compress_combine_pdfs.py sheet1.pdf sheet2.pdf sheet3.pdf -o combined.pdf
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from pypdf import PdfWriter


# Ghostscript quality presets (maps to -dPDFSETTINGS)
GS_PRESETS = {
    "screen":   "/screen",     # 72 dpi  - smallest, low quality
    "ebook":    "/ebook",      # 150 dpi - good balance for cut/fill sheets
    "printer":  "/printer",    # 300 dpi - high quality, moderate size
    "prepress": "/prepress",   # 300 dpi - highest quality
}


def find_ghostscript() -> str | None:
    """Find Ghostscript executable on the system."""
    for cmd in ["gs", "gswin64c", "gswin32c"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None


def compress_pdf(gs_cmd: str, input_path: Path, output_path: Path,
                 dpi: int = 200, quality: str = "ebook") -> bool:
    """Compress a single PDF using Ghostscript."""
    preset = GS_PRESETS.get(quality, "/ebook")

    args = [
        gs_cmd,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS={preset}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        # Downsample color images (the heat ramp rasters)
        "-dDownsampleColorImages=true",
        f"-dColorImageResolution={dpi}",
        "-dColorImageDownsampleType=/Bicubic",
        # Downsample grayscale
        "-dDownsampleGrayImages=true",
        f"-dGrayImageResolution={dpi}",
        "-dGrayImageDownsampleType=/Bicubic",
        # Downsample mono (linework stays vector, this is for rasterized mono)
        "-dDownsampleMonoImages=true",
        f"-dMonoImageResolution={max(dpi, 300)}",
        # Compress
        "-dAutoFilterColorImages=false",
        "-dColorImageFilter=/DCTEncode",
        "-dAutoFilterGrayImages=false",
        "-dGrayImageFilter=/DCTEncode",
        # Optimize
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: Ghostscript error on {input_path.name}: {result.stderr[:200]}")
        return False
    return True


def get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def collect_pdfs(inputs: list[str]) -> list[Path]:
    """Collect PDF files from input arguments (files and/or folders)."""
    pdfs = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            pdfs.extend(sorted(p.glob("*.pdf")))
        elif p.is_file() and p.suffix.lower() == ".pdf":
            pdfs.append(p)
        else:
            print(f"  Skipping: {item}")
    return pdfs


def main():
    parser = argparse.ArgumentParser(
        description="Compress and combine Civil3D sheet set PDFs"
    )
    parser.add_argument(
        "inputs", nargs="+",
        help="PDF files and/or folders containing PDFs"
    )
    parser.add_argument(
        "-o", "--output", default="combined_compressed.pdf",
        help="Output filename (default: combined_compressed.pdf)"
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help="Target raster DPI - 150 for small files, 300 for print quality (default: 200)"
    )
    parser.add_argument(
        "--quality", choices=GS_PRESETS.keys(), default="ebook",
        help="Ghostscript quality preset (default: ebook)"
    )
    parser.add_argument(
        "--no-compress", action="store_true",
        help="Skip compression, just combine PDFs"
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    # Collect input PDFs
    pdfs = collect_pdfs(args.inputs)
    if not pdfs:
        print("ERROR: No PDF files found in the specified inputs.")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s):")
    total_input_mb = 0
    for p in pdfs:
        size = get_file_size_mb(p)
        total_input_mb += size
        print(f"  {p.name:40s}  {size:8.2f} MB")
    print(f"  {'TOTAL INPUT':40s}  {total_input_mb:8.2f} MB")
    print()

    # Find Ghostscript
    gs_cmd = None if args.no_compress else find_ghostscript()
    if not args.no_compress and gs_cmd is None:
        print("WARNING: Ghostscript not found. Combining without compression.")
        print("  Install: apt install ghostscript (Linux) / choco install ghostscript (Windows)")
        print()

    # Process
    compressed_pdfs = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, pdf in enumerate(pdfs, 1):
            if gs_cmd and not args.no_compress:
                compressed_path = Path(tmpdir) / f"compressed_{i:03d}.pdf"
                print(f"[{i}/{len(pdfs)}] Compressing {pdf.name}...", end=" ", flush=True)

                if compress_pdf(gs_cmd, pdf, compressed_path, args.dpi, args.quality):
                    old_size = get_file_size_mb(pdf)
                    new_size = get_file_size_mb(compressed_path)
                    reduction = (1 - new_size / old_size) * 100 if old_size > 0 else 0
                    print(f"{old_size:.1f} MB → {new_size:.1f} MB ({reduction:.0f}% reduction)")
                    compressed_pdfs.append(compressed_path)
                else:
                    print("failed, using original")
                    compressed_pdfs.append(pdf)
            else:
                compressed_pdfs.append(pdf)

        # Combine all PDFs
        print(f"\nCombining {len(compressed_pdfs)} PDFs into {output_path}...")
        writer = PdfWriter()
        for pdf in compressed_pdfs:
            writer.append(str(pdf))

        with open(output_path, "wb") as f:
            writer.write(f)

    # Summary
    final_size = get_file_size_mb(output_path)
    total_reduction = (1 - final_size / total_input_mb) * 100 if total_input_mb > 0 else 0
    print(f"\nDone!")
    print(f"  Input:  {total_input_mb:.2f} MB ({len(pdfs)} files)")
    print(f"  Output: {final_size:.2f} MB → {output_path}")
    print(f"  Total reduction: {total_reduction:.0f}%")


if __name__ == "__main__":
    main()
