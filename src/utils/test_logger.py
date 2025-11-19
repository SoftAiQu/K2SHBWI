#!/usr/bin/env python3
"""
K2SHBWI Test Logger Module
Real-time logging for compression, SSIM, and performance metrics.

Captures:
- Timestamps (ISO format)
- File sizes (original vs compressed)
- Compression ratios
- Processing times (milliseconds)
- Algorithm names
- Test results (PASS/FAIL)
- SSIM scores
- Error details

Output: JSON (machine-readable) + TXT (human-readable) + SHA256 hash
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from typing import Dict, Any, List, Optional, Union
import time


class TestLogger:
    """
    Real-time logger for K2SHBWI tests and benchmarks.
    
    Captures metrics and writes to JSON + TXT formats in /logs/ directory.
    Each log includes timestamp, all metrics, and SHA256 verification hash.
    """
    
    def __init__(self, logger_name: str, log_type: str = "test"):
        """
        Initialize logger instance.
        
        Args:
            logger_name: Name for this logger (e.g., "benchmark_compression")
            log_type: Type of log - "benchmark", "test", or "cli"
        
        Raises:
            ValueError: If log_type is not valid
        """
        self.logger_name = logger_name
        self.log_type = log_type
        
        if log_type not in ["benchmark", "test", "cli"]:
            raise ValueError(f"log_type must be 'benchmark', 'test', or 'cli', got '{log_type}'")
        
        # Generate timestamp for filename (ISO format without colons)
        now = datetime.now(timezone.utc)
        self.timestamp_iso = now.isoformat()
        self.timestamp_filename = now.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # ms precision
        
        # Metrics storage
        self.metrics: List[Dict[str, Any]] = []
        self.summary_data: Dict[str, Any] = {}
        self.errors: List[str] = []
        
        # Setup directories
        self.base_logs_dir = Path(__file__).parent.parent.parent / "logs"
        
        if log_type == "benchmark":
            self.log_dir = self.base_logs_dir / "benchmark_results"
        elif log_type == "test":
            self.log_dir = self.base_logs_dir / "test_runs"
        else:  # cli
            self.log_dir = self.base_logs_dir / "cli_runs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        self.filename_base = f"{logger_name}_{self.timestamp_filename}"
        self.json_file = self.log_dir / f"{self.filename_base}.json"
        self.txt_file = self.log_dir / f"{self.filename_base}.txt"
        self.hash_file = self.log_dir / f"{self.filename_base}.json.hash"
    
    def log_compression_metric(
        self,
        file_name: str,
        original_bytes: int,
        compressed_bytes: int,
        algorithm: str,
        processing_time_ms: float,
        status: str = "SUCCESS",
        error_msg: Optional[str] = None
    ) -> None:
        """
        Log compression metric.
        
        Args:
            file_name: Name of file being compressed
            original_bytes: Size before compression
            compressed_bytes: Size after compression
            algorithm: Algorithm used (ZLIB, BROTLI, LZMA, ZSTD, etc)
            processing_time_ms: Time taken in milliseconds
            status: SUCCESS or FAIL
            error_msg: Error message if status is FAIL
        """
        # Calculate compression ratio
        if original_bytes > 0:
            compression_ratio = ((original_bytes - compressed_bytes) / original_bytes) * 100
        else:
            compression_ratio = 0.0
        
        metric = {
            "type": "compression",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_name": file_name,
            "original_bytes": original_bytes,
            "compressed_bytes": compressed_bytes,
            "compression_ratio_percent": round(compression_ratio, 2),
            "algorithm": algorithm,
            "processing_time_ms": round(processing_time_ms, 2),
            "status": status
        }
        
        if error_msg:
            metric["error"] = error_msg
            self.errors.append(f"{file_name}: {error_msg}")
        
        self.metrics.append(metric)
    
    def log_test_result(
        self,
        test_name: str,
        status: str,
        input_bytes: int,
        output_bytes: int,
        processing_time_ms: float,
        compression_type: str = "UNKNOWN",
        error_msg: Optional[str] = None
    ) -> None:
        """
        Log test result.
        
        Args:
            test_name: Name of test
            status: PASS, FAIL, or SKIP
            input_bytes: Input data size
            output_bytes: Output data size
            processing_time_ms: Time taken in milliseconds
            compression_type: Type of compression tested
            error_msg: Error message if FAIL
        """
        # Calculate compression ratio
        if input_bytes > 0:
            compression_ratio = ((input_bytes - output_bytes) / input_bytes) * 100
        else:
            compression_ratio = 0.0
        
        metric = {
            "type": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_name": test_name,
            "status": status,
            "input_bytes": input_bytes,
            "output_bytes": output_bytes,
            "compression_ratio_percent": round(compression_ratio, 2),
            "compression_type": compression_type,
            "processing_time_ms": round(processing_time_ms, 2)
        }
        
        if error_msg:
            metric["error"] = error_msg
            self.errors.append(f"{test_name}: {error_msg}")
        
        self.metrics.append(metric)
    
    def log_ssim_metric(
        self,
        image_size: str,
        score: float,
        processing_time_ms: float,
        comparison_type: str = "identical",
        method: str = "skimage"
    ) -> None:
        """
        Log SSIM (Structural Similarity) metric.
        
        Args:
            image_size: Image dimensions (e.g., "128x128", "256x256")
            score: SSIM score (0.0 to 1.0)
            processing_time_ms: Time taken in milliseconds
            comparison_type: "identical" or "different"
            method: Implementation method (skimage, numpy, pure_python)
        """
        metric = {
            "type": "ssim",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_size": image_size,
            "ssim_score": round(score, 6),
            "comparison_type": comparison_type,
            "processing_time_ms": round(processing_time_ms, 2),
            "method": method
        }
        
        self.metrics.append(metric)
    
    def log_cli_command(
        self,
        command: str,
        input_file: str,
        output_file: str,
        input_bytes: int,
        output_bytes: int,
        algorithm_used: str,
        processing_time_ms: float,
        status: str = "SUCCESS",
        error_msg: Optional[str] = None
    ) -> None:
        """
        Log CLI command execution.
        
        Args:
            command: CLI command (create, decode, encode, etc)
            input_file: Input file name
            output_file: Output file name
            input_bytes: Input file size in bytes
            output_bytes: Output file size in bytes
            algorithm_used: Algorithm selected
            processing_time_ms: Time taken in milliseconds
            status: SUCCESS or FAIL
            error_msg: Error message if FAIL
        """
        # Calculate compression ratio
        if input_bytes > 0:
            compression_ratio = ((input_bytes - output_bytes) / input_bytes) * 100
        else:
            compression_ratio = 0.0
        
        metric = {
            "type": "cli_command",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "input_file": input_file,
            "output_file": output_file,
            "input_bytes": input_bytes,
            "output_bytes": output_bytes,
            "compression_ratio_percent": round(compression_ratio, 2),
            "algorithm_used": algorithm_used,
            "processing_time_ms": round(processing_time_ms, 2),
            "status": status
        }
        
        if error_msg:
            metric["error"] = error_msg
            self.errors.append(f"{command}: {error_msg}")
        
        self.metrics.append(metric)
    
    def add_summary(self, summary: Dict[str, Any]) -> None:
        """
        Add summary statistics to log.
        
        Args:
            summary: Dictionary with summary data
        """
        self.summary_data.update(summary)
    
    def _generate_hash(self, json_content: str) -> str:
        """
        Generate SHA256 hash of JSON content.
        
        Args:
            json_content: JSON string to hash
        
        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(json_content.encode()).hexdigest()
    
    def save_log(self) -> Dict[str, Path]:
        """
        Save log as JSON, TXT, and verify with hash.
        
        Returns:
            Dictionary with paths: {"json": Path, "txt": Path, "hash": Path}
        """
        if not self.metrics:
            raise ValueError("No metrics to save. Add metrics before saving log.")
        
        # Calculate aggregate statistics
        total_original = sum(m.get("original_bytes", 0) or m.get("input_bytes", 0) 
                            for m in self.metrics if m.get("type") != "ssim")
        total_compressed = sum(m.get("compressed_bytes", 0) or m.get("output_bytes", 0) 
                              for m in self.metrics if m.get("type") != "ssim")
        
        total_time = sum(m.get("processing_time_ms", 0) for m in self.metrics)
        
        if total_original > 0:
            avg_compression = ((total_original - total_compressed) / total_original) * 100
        else:
            avg_compression = 0.0
        
        # Build complete log object
        log_object = {
            "timestamp": self.timestamp_iso,
            "logger_name": self.logger_name,
            "log_type": self.log_type,
            "system_info": {
                "python_version": self._get_python_version(),
                "platform": self._get_platform()
            },
            "metrics": self.metrics,
            "summary": {
                "total_metrics": len(self.metrics),
                "total_original_bytes": total_original,
                "total_compressed_bytes": total_compressed,
                "average_compression_ratio_percent": round(avg_compression, 2),
                "total_processing_time_ms": round(total_time, 2),
                "error_count": len(self.errors),
                **self.summary_data
            }
        }
        
        if self.errors:
            log_object["errors"] = self.errors
        
        # Save JSON
        json_content = json.dumps(log_object, indent=2)
        with open(self.json_file, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        # Save TXT (human-readable)
        txt_content = self._generate_txt_report(log_object)
        with open(self.txt_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        # Generate and save hash
        file_hash = self._generate_hash(json_content)
        with open(self.hash_file, 'w', encoding='utf-8') as f:
            f.write(f"{file_hash}\n")
        
        return {
            "json": self.json_file,
            "txt": self.txt_file,
            "hash": self.hash_file
        }
    
    def _generate_txt_report(self, log_object: Dict[str, Any]) -> str:
        """
        Generate human-readable text report.
        
        Args:
            log_object: Complete log object
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("K2SHBWI TEST LOG REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Header info
        lines.append(f"Timestamp: {log_object['timestamp']}")
        lines.append(f"Logger: {log_object['logger_name']}")
        lines.append(f"Type: {log_object['log_type']}")
        lines.append("")
        
        # System info
        lines.append("System Information:")
        lines.append(f"  Python: {log_object['system_info']['python_version']}")
        lines.append(f"  Platform: {log_object['system_info']['platform']}")
        lines.append("")
        
        # Summary
        summary = log_object['summary']
        lines.append("Summary:")
        lines.append(f"  Total Metrics: {summary['total_metrics']}")
        lines.append(f"  Original Bytes: {summary['total_original_bytes']:,}")
        lines.append(f"  Compressed Bytes: {summary['total_compressed_bytes']:,}")
        lines.append(f"  Average Compression: {summary['average_compression_ratio_percent']:.2f}%")
        lines.append(f"  Total Time: {summary['total_processing_time_ms']:.2f}ms")
        lines.append(f"  Errors: {summary['error_count']}")
        lines.append("")
        
        # Metrics
        lines.append("Detailed Metrics:")
        lines.append("-" * 80)
        
        for i, metric in enumerate(log_object['metrics'], 1):
            lines.append(f"\n[{i}] {metric.get('type', 'UNKNOWN').upper()}")
            lines.append(f"    Timestamp: {metric['timestamp']}")
            
            if metric.get('type') == 'compression':
                lines.append(f"    File: {metric['file_name']}")
                lines.append(f"    Original: {metric['original_bytes']:,} bytes")
                lines.append(f"    Compressed: {metric['compressed_bytes']:,} bytes")
                lines.append(f"    Ratio: {metric['compression_ratio_percent']:.2f}%")
                lines.append(f"    Algorithm: {metric['algorithm']}")
                lines.append(f"    Time: {metric['processing_time_ms']:.2f}ms")
                lines.append(f"    Status: {metric['status']}")
            
            elif metric.get('type') == 'test':
                lines.append(f"    Test: {metric['test_name']}")
                lines.append(f"    Input: {metric['input_bytes']:,} bytes")
                lines.append(f"    Output: {metric['output_bytes']:,} bytes")
                lines.append(f"    Ratio: {metric['compression_ratio_percent']:.2f}%")
                lines.append(f"    Type: {metric['compression_type']}")
                lines.append(f"    Time: {metric['processing_time_ms']:.2f}ms")
                lines.append(f"    Status: {metric['status']}")
            
            elif metric.get('type') == 'ssim':
                lines.append(f"    Size: {metric['image_size']}")
                lines.append(f"    SSIM Score: {metric['ssim_score']:.6f}")
                lines.append(f"    Type: {metric['comparison_type']}")
                lines.append(f"    Method: {metric['method']}")
                lines.append(f"    Time: {metric['processing_time_ms']:.2f}ms")
            
            elif metric.get('type') == 'cli_command':
                lines.append(f"    Command: {metric['command']}")
                lines.append(f"    Input: {metric['input_file']} ({metric['input_bytes']:,} bytes)")
                lines.append(f"    Output: {metric['output_file']} ({metric['output_bytes']:,} bytes)")
                lines.append(f"    Ratio: {metric['compression_ratio_percent']:.2f}%")
                lines.append(f"    Algorithm: {metric['algorithm_used']}")
                lines.append(f"    Time: {metric['processing_time_ms']:.2f}ms")
                lines.append(f"    Status: {metric['status']}")
            
            if metric.get('error'):
                lines.append(f"    ERROR: {metric['error']}")
        
        # Errors
        if log_object.get('errors'):
            lines.append("\n" + "=" * 80)
            lines.append("ERRORS:")
            lines.append("=" * 80)
            for error in log_object['errors']:
                lines.append(f"  - {error}")
        
        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_python_version() -> str:
        """Get Python version."""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    @staticmethod
    def _get_platform() -> str:
        """Get platform information."""
        import platform
        return f"{platform.system()} {platform.release()}"
    
    def get_log_paths(self) -> Dict[str, Path]:
        """
        Get paths to log files without saving.
        
        Returns:
            Dictionary with paths: {"json": Path, "txt": Path, "hash": Path}
        """
        return {
            "json": self.json_file,
            "txt": self.txt_file,
            "hash": self.hash_file
        }


def verify_log_hash(json_file: Union[str, Path], hash_file: Union[str, Path]) -> bool:
    """
    Verify integrity of a log file using its hash.
    
    Args:
        json_file: Path to JSON log file
        hash_file: Path to hash file
    
    Returns:
        True if hash matches, False otherwise
    
    Raises:
        FileNotFoundError: If files don't exist
    """
    json_file = Path(json_file)
    hash_file = Path(hash_file)
    
    if not json_file.exists():
        raise FileNotFoundError(f"Log file not found: {json_file}")
    if not hash_file.exists():
        raise FileNotFoundError(f"Hash file not found: {hash_file}")
    
    # Read hash file
    with open(hash_file, 'r', encoding='utf-8') as f:
        stored_hash = f.read().strip()
    
    # Read JSON file and recalculate hash
    with open(json_file, 'r', encoding='utf-8') as f:
        json_content = f.read()
    
    calculated_hash = hashlib.sha256(json_content.encode()).hexdigest()
    
    return stored_hash == calculated_hash


if __name__ == "__main__":
    # Example usage
    logger = TestLogger("example_compression", log_type="benchmark")
    
    logger.log_compression_metric(
        file_name="sample.png",
        original_bytes=1382,
        compressed_bytes=1353,
        algorithm="BROTLI",
        processing_time_ms=118.76
    )
    
    logger.log_compression_metric(
        file_name="sample.png",
        original_bytes=1382,
        compressed_bytes=1383,
        algorithm="ZLIB",
        processing_time_ms=1.43
    )
    
    logger.add_summary({"dataset": "test_images", "test_count": 2})
    
    paths = logger.save_log()
    print(f"✅ Logs saved:")
    print(f"  JSON: {paths['json']}")
    print(f"  TXT: {paths['txt']}")
    print(f"  Hash: {paths['hash']}")
    
    # Verify hash
    is_valid = verify_log_hash(paths['json'], paths['hash'])
    print(f"✅ Hash verification: {'VALID' if is_valid else 'INVALID'}")
