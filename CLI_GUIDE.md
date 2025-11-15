# K2SHBWI CLI Guide - Complete Command Reference

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Basic Syntax](#basic-syntax)
3. [All Commands](#all-commands)
4. [Examples](#examples)
5. [Tips & Tricks](#tips--tricks)

## Installation & Setup

### 1. Create Virtual Environment
```bash
cd K2SHBWI
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
.\venv\Scripts\activate
```

**Unix/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python tools/cli_click.py --version
# Output: k2shbwi, version 1.0.0

python tools/cli_click.py --help
# Shows all available commands
```

## Basic Syntax

```bash
python tools/cli_click.py [COMMAND] [OPTIONS] [ARGUMENTS]
```

**Global Options:**
- `--version` : Show version and exit
- `--help` : Show help message and exit

**Command Syntax:**
```bash
python tools/cli_click.py COMMAND [OPTIONS]
```

**Getting Help:**
```bash
# Global help
python tools/cli_click.py --help

# Command-specific help
python tools/cli_click.py COMMAND --help

# Example
python tools/cli_click.py create --help
```

## All Commands

### 1. CREATE - Create K2SHBWI from Image

**Purpose:** Convert an image to K2SHBWI format with optional metadata

**Syntax:**
```bash
python tools/cli_click.py create [OPTIONS]
```

**Options:**
```
-i, --input TEXT         Input image file path [required]
-o, --output TEXT        Output K2SHBWI file path [required]
-t, --title TEXT         Image title [optional]
-d, --description TEXT   Image description [optional]
-m, --metadata TEXT      JSON metadata string [optional]
-v, --verbose           Verbose output
--help                   Show help message
```

**Examples:**
```bash
# Simple creation
python tools/cli_click.py create -i photo.png -o photo.k2sh

# With title and description
python tools/cli_click.py create -i photo.png -o photo.k2sh \
  -t "My Photo" -d "Taken in 2025"

# With JSON metadata
python tools/cli_click.py create -i photo.png -o photo.k2sh \
  -m '{"location": "Beach", "date": "2025-01-01"}'

# Verbose mode
python tools/cli_click.py create -i photo.png -o photo.k2sh -v
```

**Supported Image Formats:**
- PNG, JPEG, BMP, GIF, TIFF, WEBP, and more

---

### 2. INFO - Display File Information

**Purpose:** Show detailed information about a K2SHBWI file

**Syntax:**
```bash
python tools/cli_click.py info [OPTIONS] FILE
```

**Arguments:**
```
FILE  K2SHBWI file path [required]
```

**Options:**
```
-v, --verbose  Verbose output
--help         Show help message
```

**Examples:**
```bash
# Display info
python tools/cli_click.py info photo.k2sh

# Verbose mode (shows more details)
python tools/cli_click.py info photo.k2sh -v
```

**Output Includes:**
- Filename and file size
- Metadata (title, description, custom fields)
- Hotspots list and descriptions

---

### 3. VALIDATE - Validate File Integrity

**Purpose:** Check if K2SHBWI file is valid and uncorrupted

**Syntax:**
```bash
python tools/cli_click.py validate [OPTIONS] FILE
```

**Arguments:**
```
FILE  K2SHBWI file path [required]
```

**Options:**
```
-v, --verbose  Verbose output
--help         Show help message
```

**Examples:**
```bash
# Basic validation
python tools/cli_click.py validate photo.k2sh

# Verbose validation
python tools/cli_click.py validate photo.k2sh -v
```

**Checks Performed:**
- Valid header format
- Image data presence
- Metadata consistency
- Hotspots validity

---

### 4. BATCH - Batch Process Images

**Purpose:** Convert multiple images to K2SHBWI format at once

**Syntax:**
```bash
python tools/cli_click.py batch [OPTIONS]
```

**Options:**
```
-i, --input-dir TEXT   Input directory with images [required]
-o, --output-dir TEXT  Output directory for K2SHBWI files [required]
-v, --verbose         Verbose output
--help                Show help message
```

**Examples:**
```bash
# Batch process
python tools/cli_click.py batch -i input_images -o output_k2sh

# With verbose output
python tools/cli_click.py batch -i input_images -o output_k2sh -v
```

**Supported Formats:**
Processes all images: .png, .jpg, .jpeg, .bmp, .gif, .tiff

**Output:**
Reports success/failure count for all processed files

---

### 5. ENCODE - Low-Level Encode

**Purpose:** Encode image without metadata (alternative to create)

**Syntax:**
```bash
python tools/cli_click.py encode [OPTIONS]
```

**Options:**
```
-i, --input TEXT   Input image file [required]
-o, --output TEXT  Output K2SHBWI file [required]
-v, --verbose     Verbose output
--help            Show help message
```

**Examples:**
```bash
# Basic encoding
python tools/cli_click.py encode -i photo.png -o photo.k2sh

# Verbose mode
python tools/cli_click.py encode -i photo.png -o photo.k2sh -v
```

**Difference from CREATE:**
- `encode`: Image only, no metadata
- `create`: Image + optional metadata

---

### 6. DECODE - Extract Image

**Purpose:** Extract original image from K2SHBWI file

**Syntax:**
```bash
python tools/cli_click.py decode [OPTIONS] FILE
```

**Arguments:**
```
FILE  K2SHBWI file path [required]
```

**Options:**
```
-o, --output TEXT  Output image file path [required]
-v, --verbose     Verbose output
--help            Show help message
```

**Examples:**
```bash
# Extract image
python tools/cli_click.py decode photo.k2sh -o extracted.png

# Verbose extraction
python tools/cli_click.py decode photo.k2sh -o extracted.png -v
```

---

### 7. CONVERT - Convert to Other Formats

**Purpose:** Convert K2SHBWI file to HTML, PDF, or PowerPoint

**Syntax:**
```bash
python tools/cli_click.py convert [OPTIONS] FILE
```

**Arguments:**
```
FILE  K2SHBWI file path [required]
```

**Options:**
```
-f, --format [html|pdf|pptx]  Output format [required]
-o, --output TEXT            Output file path [required]
-v, --verbose               Verbose output
--help                      Show help message
```

**Examples:**
```bash
# Convert to HTML
python tools/cli_click.py convert photo.k2sh -f html -o viewer.html

# Convert to PDF
python tools/cli_click.py convert photo.k2sh -f pdf -o report.pdf

# Convert to PowerPoint
python tools/cli_click.py convert photo.k2sh -f pptx -o presentation.pptx

# Verbose conversion
python tools/cli_click.py convert photo.k2sh -f html -o viewer.html -v
```

**Format Details:**

#### HTML
- Interactive web viewer
- Embedded image (no external files)
- Hotspot overlays with hover effects
- File size: ~8 KB
- Open directly in any web browser

#### PDF
- Professional document format
- Formatted metadata table
- Hotspots information
- Suitable for printing
- File size: ~13 KB

#### PPTX
- Multi-slide PowerPoint presentation
- Separate slides for: title, image, hotspots, metadata
- Professional formatting
- File size: ~30 KB

---

### 8. VIEW - Open in Viewer

**Purpose:** Open K2SHBWI file in interactive viewer

**Syntax:**
```bash
python tools/cli_click.py view [OPTIONS] FILE
```

**Arguments:**
```
FILE  K2SHBWI file path [required]
```

**Options:**
```
-t, --type [web|desktop]  Viewer type (default: web)
-v, --verbose            Verbose output
--help                   Show help message
```

**Examples:**
```bash
# View in web browser (default)
python tools/cli_click.py view photo.k2sh

# Explicitly use web viewer
python tools/cli_click.py view photo.k2sh -t web

# View in desktop GUI
python tools/cli_click.py view photo.k2sh -t desktop

# Verbose mode
python tools/cli_click.py view photo.k2sh -v
```

**Viewer Types:**

#### Web Viewer
- Opens interactive HTML in default browser
- Click on hotspots to see details
- Responsive design
- No external files needed

#### Desktop Viewer
- Native GUI using Tkinter
- Left side: Image display
- Right side: File info and hotspots list
- Shows metadata and hotspot details

---

## Examples

### Example 1: Create and Convert to HTML

```bash
# Create K2SHBWI from image
python tools/cli_click.py create -i beach.png -o beach.k2sh \
  -t "Beach Photo" -d "Taken in summer 2025"

# Verify it was created
python tools/cli_click.py validate beach.k2sh

# Convert to HTML
python tools/cli_click.py convert beach.k2sh -f html -o beach.html

# View in browser
python tools/cli_click.py view beach.k2sh
```

### Example 2: Batch Process Photos

```bash
# Create output directory
mkdir processed_photos

# Batch process all images in a directory
python tools/cli_click.py batch \
  -i C:\Users\YourName\Pictures \
  -o processed_photos \
  -v

# View results
ls processed_photos/
```

### Example 3: Create Complete Presentation

```bash
# Create from image with metadata
python tools/cli_click.py create -i diagram.png -o diagram.k2sh \
  -t "System Architecture" \
  -d "2025 System Design" \
  -m '{"version": "2.0", "team": "Engineering"}'

# Generate all three format outputs
python tools/cli_click.py convert diagram.k2sh -f html -o diagram_view.html
python tools/cli_click.py convert diagram.k2sh -f pdf -o diagram_report.pdf
python tools/cli_click.py convert diagram.k2sh -f pptx -o diagram_slides.pptx

# Now you have:
# - diagram_view.html: Interactive web viewer
# - diagram_report.pdf: Professional report
# - diagram_slides.pptx: Presentation slides
```

### Example 4: Extract and Validate

```bash
# Check file info
python tools/cli_click.py info photo.k2sh -v

# Validate integrity
python tools/cli_click.py validate photo.k2sh

# Extract original image
python tools/cli_click.py decode photo.k2sh -o extracted.png

# Verify extracted image
ls -lh extracted.png
```

---

## Tips & Tricks

### Tip 1: Using Verbose Mode
Always use `-v` flag when debugging:
```bash
python tools/cli_click.py create -i photo.png -o photo.k2sh -v
```
This shows file sizes, processing steps, and timing information.

### Tip 2: Getting Command Help
Quick access to any command's help:
```bash
python tools/cli_click.py COMMAND --help

# Examples:
python tools/cli_click.py create --help
python tools/cli_click.py convert --help
python tools/cli_click.py batch --help
```

### Tip 3: Working with Paths
Use absolute paths to avoid issues:
```bash
# Better (absolute path)
python tools/cli_click.py create \
  -i C:\full\path\to\image.png \
  -o C:\full\path\to\output.k2sh

# Also works (relative to current directory)
python tools/cli_click.py create -i .\images\photo.png -o .\output\photo.k2sh
```

### Tip 4: Batch Processing Large Directories
For many files, use verbose mode to track progress:
```bash
python tools/cli_click.py batch -i large_folder -o output -v
# Shows each file being processed
```

### Tip 5: JSON Metadata
Pass complex metadata as JSON:
```bash
python tools/cli_click.py create -i photo.png -o photo.k2sh \
  -m '{"location": "NYC", "date": "2025-01-01", "camera": "Canon"}'
```

### Tip 6: Multiple Conversions
Create all formats at once:
```bash
FILE="photo.k2sh"
python tools/cli_click.py convert $FILE -f html -o $FILE.html
python tools/cli_click.py convert $FILE -f pdf -o $FILE.pdf
python tools/cli_click.py convert $FILE -f pptx -o $FILE.pptx
```

### Tip 7: Validation Before Processing
Always validate before important operations:
```bash
python tools/cli_click.py validate photo.k2sh && \
  python tools/cli_click.py convert photo.k2sh -f html -o photo.html
```

### Tip 8: Use Scripts for Repeated Tasks
Create batch scripts for common operations:

**Windows batch file (process.bat):**
```batch
@echo off
python tools/cli_click.py batch -i %1 -o %2 -v
pause
```

Usage: `process.bat input_folder output_folder`

**Bash script (process.sh):**
```bash
#!/bin/bash
python tools/cli_click.py batch -i $1 -o $2 -v
```

Usage: `bash process.sh input_folder output_folder`

---

## Common Workflows

### Workflow 1: Simple Image to K2SHBWI
```bash
python tools/cli_click.py create -i image.png -o image.k2sh
```

### Workflow 2: Create and View
```bash
python tools/cli_click.py create -i image.png -o image.k2sh && \
python tools/cli_click.py view image.k2sh
```

### Workflow 3: Create, Convert to HTML, and Open
```bash
python tools/cli_click.py create -i image.png -o image.k2sh && \
python tools/cli_click.py convert image.k2sh -f html -o image.html && \
start image.html  # Windows
# open image.html  # Mac
# xdg-open image.html  # Linux
```

### Workflow 4: Batch Process with Reports
```bash
python tools/cli_click.py batch -i input -o output -v && \
python tools/cli_click.py info output/*.k2sh
```

### Workflow 5: Backup and Extract
```bash
python tools/cli_click.py validate image.k2sh && \
python tools/cli_click.py decode image.k2sh -o backup.png
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error (missing args, file not found, etc.) |
| 2    | Usage error (wrong arguments) |

---

## Environment Variables

No specific environment variables required, but you can customize Python:

```bash
# Use specific Python version
C:\Python312\python.exe tools/cli_click.py --help

# Set Python path
set PYTHONPATH=%CD%;%PYTHONPATH%
python tools/cli_click.py --help
```

---

## Performance Tips

1. **Batch Processing**: Use `batch` command instead of `create` in loop
2. **Verbose Mode**: Disable for production (slightly faster)
3. **Conversions**: HTML is fastest (~50ms), PPTX is slowest (~150ms)
4. **Large Images**: May take longer, consider resizing first

---

For more information, see:
- Main README: `README.md`
- Test Results: `TEST_RESULTS.json`
- Source Code: `tools/cli_click.py`

**Last Updated:** November 16, 2025
