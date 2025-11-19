#!/usr/bin/env python3
"""
K2SHBWI Click-based CLI - Teacher's improved version
Provides 8 main commands with better UX and structured output

Now with real-time logging:
  - Metrics logged to /logs/cli_runs/
  - JSON, TXT, and hash files generated
  - Command execution times tracked
  - File sizes and compression ratios recorded
  - Add --log flag to any command to enable detailed logging
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import io
import time

import click
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
from src.converters.html_converter import HTMLConverter
from src.converters.pdf_converter import PDFConverter
from src.converters.pptx_converter import PPTXConverter
from src.viewers.web_viewer import WebViewer
from src.viewers.desktop_viewer import DesktopViewer
from src.utils.test_logger import TestLogger


# ============================================================================
# CLI GROUP AND HELPER FUNCTIONS
# ============================================================================

# Global logger instance
_logger: Optional[TestLogger] = None
_enable_logging = False


@click.group()
@click.version_option(version='1.0.0', prog_name='k2shbwi')
@click.option('--log', is_flag=True, help='Enable detailed metrics logging')
def cli(log):
    """K2SHBWI CLI - Advanced image metadata and hotspot management tool."""
    global _logger, _enable_logging
    _enable_logging = log
    if _enable_logging:
        _logger = TestLogger(logger_name="cli_commands", log_type="cli")


def print_ok(message: str):
    """Print success message."""
    click.echo(click.style(f"[OK] {message}", fg='green'))


def print_error(message: str):
    """Print error message."""
    click.echo(click.style(f"[ERROR] {message}", fg='red'))


def print_info(message: str):
    """Print info message."""
    click.echo(click.style(f"[INFO] {message}", fg='blue'))


# ============================================================================
# PHASE 3: COMMAND 1 - CREATE
# ============================================================================

@cli.command()
@click.option('-i', '--input', required=True, type=click.Path(exists=True), 
              help='Input image file path')
@click.option('-o', '--output', required=True, type=click.Path(),
              help='Output K2SHBWI file path')
@click.option('-t', '--title', default='', help='Image title')
@click.option('-d', '--description', default='', help='Image description')
@click.option('-m', '--metadata', default='{}', help='JSON metadata string')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def create(input, output, title, description, metadata, verbose):
    """Create a K2SHBWI file from an image with optional metadata."""
    global _logger, _enable_logging
    command_start = time.perf_counter()
    input_size = os.path.getsize(input)
    
    try:
        if verbose:
            print_info(f"Creating K2SHBWI from: {input}")
        
        encoder = K2SHBWIEncoder()
        
        # Parse metadata
        meta_dict = {}
        if metadata != '{}':
            meta_dict = json.loads(metadata)
        
        if title:
            meta_dict['title'] = title
        if description:
            meta_dict['description'] = description
        
        # Set metadata
        for key, value in meta_dict.items():
            encoder.metadata.__dict__[key] = value
        
        # Set the image and encode
        encoder.set_image(input)
        encoder.encode(output)
        
        output_size = os.path.getsize(output)
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        
        if verbose:
            print_info(f"Output file size: {output_size} bytes")
        
        # Log metrics if logging enabled
        if _enable_logging and _logger:
            compression_ratio = 100.0 - (output_size / input_size * 100) if input_size > 0 else 0
            _logger.log_cli_command(
                command="create",
                input_file=input,
                output_file=output,
                input_bytes=input_size,
                output_bytes=output_size,
                algorithm_used="K2SHBWI_ENCODE",
                status="SUCCESS",
                processing_time_ms=elapsed_ms
            )
        
        print_ok(f"Created: {output}")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="create",
                input_file=input,
                output_file=output,
                input_bytes=input_size,
                output_bytes=0,
                algorithm_used="K2SHBWI_ENCODE",
                status="FAILED",
                processing_time_ms=elapsed_ms,
                error_msg=str(e)
            )
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 2 - INFO
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def info(file, verbose):
    """Display information about a K2SHBWI file."""
    try:
        if verbose:
            print_info(f"Reading file: {file}")
        
        decoder = K2SHBWIDecoder()
        decoder.decode(file)
        
        # Get metadata and hotspots
        metadata = decoder.get_metadata()
        hotspots = decoder.get_hotspots()
        
        # Display header info
        click.echo(f"\nFile Information:")
        click.echo(f"  Filename: {os.path.basename(file)}")
        click.echo(f"  File Size: {os.path.getsize(file)} bytes")
        
        # Display metadata
        if metadata:
            click.echo(f"\nMetadata:")
            for key, value in metadata.items():
                click.echo(f"  {key}: {value}")
        
        # Display hotspots
        if hotspots:
            click.echo(f"\nHotspots ({len(hotspots)}):")
            for i, hotspot in enumerate(hotspots, 1):
                click.echo(f"  {i}. {hotspot.get('title', 'Untitled')}")
                if 'description' in hotspot:
                    click.echo(f"     {hotspot['description']}")
        
        print_ok("File read successfully")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 3 - VALIDATE
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def validate(file, verbose):
    """Validate a K2SHBWI file integrity."""
    try:
        if verbose:
            print_info(f"Validating: {file}")
        
        decoder = K2SHBWIDecoder()
        decoder.decode(file)
        
        # Basic validation
        if not decoder.header:
            print_error("Invalid header")
            sys.exit(1)
        
        if decoder.image_data is None:
            print_error("No image data found")
            sys.exit(1)
        
        print_ok(f"File is VALID ({len(decoder.image_data)} bytes of image data)")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 4 - BATCH
# ============================================================================

@cli.command()
@click.option('-i', '--input-dir', type=click.Path(exists=True), required=True,
              help='Input directory with images')
@click.option('-o', '--output-dir', type=click.Path(), required=True,
              help='Output directory for K2SHBWI files')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def batch(input_dir, output_dir, verbose):
    """Batch process directory of images to K2SHBWI format."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        image_files = []
        
        for file in os.listdir(input_dir):
            if os.path.splitext(file)[1].lower() in image_extensions:
                image_files.append(os.path.join(input_dir, file))
        
        if not image_files:
            print_error("No image files found in input directory")
            sys.exit(1)
        
        successful = 0
        failed = 0
        
        for image_file in image_files:
            try:
                encoder = K2SHBWIEncoder()
                output_file = os.path.join(output_dir, 
                                          os.path.splitext(os.path.basename(image_file))[0] + '.k2sh')
                encoder.set_image(image_file)
                encoder.encode(output_file)
                successful += 1
                if verbose:
                    print_info(f"Processed: {os.path.basename(image_file)}")
            except Exception as e:
                failed += 1
                if verbose:
                    print_error(f"Failed: {os.path.basename(image_file)}: {str(e)}")
        
        print_ok(f"Successful: {successful}/{len(image_files)}")
        if failed > 0:
            click.echo(f"Failed: {failed}")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 5 - ENCODE
# ============================================================================

@cli.command()
@click.option('-i', '--input', required=True, type=click.Path(exists=True),
              help='Input image file')
@click.option('-o', '--output', required=True, type=click.Path(),
              help='Output K2SHBWI file')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def encode(input, output, verbose):
    """Low-level encode command (alias for create)."""
    global _logger, _enable_logging
    command_start = time.perf_counter()
    input_size = os.path.getsize(input)
    
    try:
        if verbose:
            print_info(f"Encoding: {input}")
        
        encoder = K2SHBWIEncoder()
        encoder.set_image(input)
        encoder.encode(output)
        
        output_size = os.path.getsize(output)
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        
        # Log metrics if logging enabled
        if _enable_logging and _logger:
            compression_ratio = 100.0 - (output_size / input_size * 100) if input_size > 0 else 0
            _logger.log_cli_command(
                command="encode",
                input_file=input,
                output_file=output,
                input_bytes=input_size,
                output_bytes=output_size,
                algorithm_used="K2SHBWI_ENCODE",
                status="SUCCESS",
                processing_time_ms=elapsed_ms
            )
        
        print_ok(f"Encoded: {output}")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="encode",
                input_file=input,
                output_file=output,
                input_bytes=input_size,
                output_bytes=0,
                algorithm_used="K2SHBWI_ENCODE",
                status="FAILED",
                processing_time_ms=elapsed_ms,
                error_msg=str(e)
            )
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 6 - DECODE
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-o', '--output', required=True, type=click.Path(),
              help='Output image file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def decode(file, output, verbose):
    """Extract image from K2SHBWI file."""
    global _logger, _enable_logging
    command_start = time.perf_counter()
    input_size = os.path.getsize(file)
    
    try:
        if verbose:
            print_info(f"Decoding: {file}")
        
        decoder = K2SHBWIDecoder()
        decoder.decode(file)
        
        # Extract image data
        image_data = decoder.image_data
        if image_data is None:
            print_error("No image data found in file")
            sys.exit(1)
        
        # Save image
        image = Image.open(io.BytesIO(image_data))
        image.save(output)
        
        output_size = os.path.getsize(output)
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        
        if verbose:
            print_info(f"Image size: {image.size}")
            print_info(f"Image format: {image.format}")
        
        # Log metrics if logging enabled
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="decode",
                input_file=file,
                output_file=output,
                input_bytes=input_size,
                output_bytes=output_size,
                algorithm_used="K2SHBWI_DECODE",
                status="SUCCESS",
                processing_time_ms=elapsed_ms
            )
        
        print_ok(f"Decoded: {output}")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="decode",
                input_file=file,
                output_file=output,
                input_bytes=input_size,
                output_bytes=0,
                algorithm_used="K2SHBWI_DECODE",
                status="FAILED",
                processing_time_ms=elapsed_ms,
                error_msg=str(e)
            )
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 7 - CONVERT
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-f', '--format', type=click.Choice(['html', 'pdf', 'pptx']),
              required=True, help='Output format')
@click.option('-o', '--output', required=True, type=click.Path(),
              help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def convert(file, format, output, verbose):
    """Convert K2SHBWI file to another format (HTML, PDF, PPTX)."""
    global _logger, _enable_logging
    command_start = time.perf_counter()
    input_size = os.path.getsize(file)
    
    try:
        if verbose:
            print_info(f"Converting to {format.upper()}: {file}")
        
        # Select converter
        if format == 'html':
            converter = HTMLConverter()
        elif format == 'pdf':
            converter = PDFConverter()
        elif format == 'pptx':
            converter = PPTXConverter()
        else:
            print_error(f"Unknown format: {format}")
            sys.exit(1)
        
        # Convert
        converter.convert(file, output)
        
        output_size = os.path.getsize(output)
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        
        # Display stats
        stats = converter.get_stats()
        if verbose:
            print_info(f"Conversion stats: {stats}")
        
        # Log metrics if logging enabled
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="convert",
                input_file=file,
                output_file=output,
                input_bytes=input_size,
                output_bytes=output_size,
                algorithm_used=f"CONVERTER_{format.upper()}",
                status="SUCCESS",
                processing_time_ms=elapsed_ms
            )
        
        print_ok(f"Converted to {format.upper()}: {output} ({output_size} bytes)")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - command_start) * 1000
        if _enable_logging and _logger:
            _logger.log_cli_command(
                command="convert",
                input_file=file,
                output_file=output,
                input_bytes=input_size,
                output_bytes=0,
                algorithm_used=f"CONVERTER_{format.upper()}",
                status="FAILED",
                processing_time_ms=elapsed_ms,
                error_msg=str(e)
            )
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PHASE 3: COMMAND 8 - VIEW
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-t', '--type', type=click.Choice(['web', 'desktop']), 
              default='web', help='Viewer type')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def view(file, type, verbose):
    """Open K2SHBWI file in viewer (web or desktop)."""
    try:
        if verbose:
            print_info(f"Opening in {type} viewer: {file}")
        
        if type == 'web':
            viewer = WebViewer()
        else:  # desktop
            viewer = DesktopViewer()
        
        result = viewer.view(file)
        
        if verbose:
            print_info(f"Viewer result: {result}")
        
        print_ok(f"Opened in {type} viewer")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# MAIN
# ============================================================================

def save_cli_logs():
    """Save CLI logs after command execution"""
    global _logger, _enable_logging
    if _enable_logging and _logger:
        _logger.add_summary({
            "cli_tool": "k2shbwi",
            "version": "1.0.0",
            "logging_enabled": True
        })
        log_paths = _logger.save_log()
        click.echo(f"\n[Logging] Metrics saved to {log_paths['json']}")


if __name__ == '__main__':
    try:
        cli()
    finally:
        save_cli_logs()
