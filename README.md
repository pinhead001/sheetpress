# sheetpress

Compresses and combines Civil3D sheet set PDFs into a single optimized file. Designed specifically for sheets containing cut/fill heat ramps, elevation banding, and slope analysis surfaces that produce oversized PDFs.

Uses Ghostscript to aggressively downsample raster content while preserving vector linework and text quality.

---

## Quick Start (Docker)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Step 1: Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/sheetpress.git
cd sheetpress
```

### Step 2: Build the Docker image

```bash
docker build -t sheetpress .
```

### Step 3: Run it

**Option A — Mount a folder of PDFs:**

```bash
# Windows (PowerShell)
docker run --rm -v "${PWD}\input:/data/input" -v "${PWD}\output:/data/output" sheetpress /data/input -o /data/output/combined.pdf --dpi 200 --quality ebook

# macOS/Linux
docker run --rm -v "$(pwd)/input:/data/input" -v "$(pwd)/output:/data/output" sheetpress /data/input -o /data/output/combined.pdf --dpi 200 --quality ebook
```

**Option B — Use docker compose (easiest):**

1. Drop your PDFs into the `input/` folder
2. Run:

```bash
docker compose up
```

3. Pick up your compressed file from `output/combined_compressed.pdf`

---

## Quality Presets

| Preset     | Raster DPI | Best For                              |
|------------|-----------|---------------------------------------|
| `screen`   | 72        | Quick review, email attachments       |
| `ebook`    | 150       | **Default** — good balance for cut/fill sheets |
| `printer`  | 300       | Print submittals, regulatory packages |
| `prepress` | 300       | Highest quality, pre-press output     |

Override the raster DPI independently with `--dpi`:

```bash
docker run --rm -v ... sheetpress /data/input -o /data/output/combined.pdf --quality printer --dpi 250
```

---

## Usage Without Docker

### Prerequisites

- Python 3.10+
- Ghostscript: `apt install ghostscript` (Linux) / `brew install ghostscript` (macOS) / `choco install ghostscript` (Windows)

### Install & Run

```bash
pip install -r requirements.txt

# Compress a folder of sheet set PDFs
python compress_combine_pdfs.py "C:\Projects\SodaButte\SheetPDFs" -o submittal_package.pdf --quality printer --dpi 300

# Compress specific sheets
python compress_combine_pdfs.py C-101.pdf C-102.pdf C-103.pdf -o package.pdf

# Just combine, no compression
python compress_combine_pdfs.py sheets/ -o combined.pdf --no-compress

# Split output into files no larger than 100 MB each
python compress_combine_pdfs.py sheets/ -o package.pdf --max-size 100
```

---

## Typical Civil3D Workflow

1. **Publish sheet set** from Civil3D → output individual PDFs to a folder
2. **Drop PDFs** into the `input/` directory (or point to your publish folder)
3. **Run the compressor:**
   ```bash
   docker compose up
   ```
4. **Grab the output** from `output/combined_compressed.pdf`

### Recommended settings by deliverable type:

| Deliverable                | Command                                          |
|----------------------------|--------------------------------------------------|
| Client review draft        | `--quality ebook --dpi 150`                      |
| Regulatory submittal       | `--quality printer --dpi 300`                    |
| Email attachment (<10 MB)  | `--quality screen --dpi 100`                     |
| Upload portal (100 MB cap) | `--quality printer --dpi 300 --max-size 100`     |
| Internal QC                | `--quality ebook --dpi 200` (default)            |

---

## Project Structure

```
sheetpress/
├── compress_combine_pdfs.py   # Main script
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Easy docker compose usage
├── requirements.txt           # Python dependencies
├── .dockerignore
├── .gitignore
├── input/                     # Drop PDFs here (gitignored)
├── output/                    # Compressed output lands here (gitignored)
└── README.md
```

---

## GitHub Setup

### Initialize and push to a new repo

```bash
# From the sheetpress/ directory
git init
git add .
git commit -m "Initial commit: PDF compressor for Civil3D sheet sets"

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/sheetpress.git
git branch -M main
git push -u origin main
```

### Track changes

```bash
# After making edits
git add -A
git commit -m "description of changes"
git push
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Ghostscript not found (Docker) | Rebuild image: `docker build --no-cache -t sheetpress .` |
| Ghostscript not found (local) | Install: `apt install ghostscript` / `choco install ghostscript` |
| Output still too large | Try `--quality screen --dpi 100`, use `--max-size 100` to split, or reduce analysis ranges in Civil3D |
| Blank/corrupted pages | Ensure Civil3D published with "AutoCAD PDF" plotter, not Adobe |
| Permission denied (Docker) | Check volume mount paths match your OS syntax |
