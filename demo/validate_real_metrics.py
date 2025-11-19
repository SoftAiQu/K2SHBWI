#!/usr/bin/env python3
"""
K2SHBWI Real Metrics Validation Script

PURPOSE:
  Validate compression claims using actual images from uploads/ folder
  Convert unverified claims to VERIFIED metrics
  Generate comparison report: claimed vs actual

USAGE:
  python validate_real_metrics.py

OUTPUT:
  - validation_results.json (raw data)
  - VALIDATION_REPORT.md (human-readable report)
  - Charts and statistics for all format articles
"""

import os
import json
import time
from pathlib import Path
from PIL import Image
import numpy as np

# Optional: if scikit-image is available
try:
    from skimage.metrics import structural_similarity as ssim, peak_signal_noise_ratio as psnr
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False
    print("⚠️  WARNING: scikit-image not found. Using basic metrics only.")
    print("   Install with: pip install scikit-image")


class MetricsValidator:
    """
    Validate K2SHBWI compression using real image pairs
    """
    
    def __init__(self, uploads_path="uploads/"):
        self.uploads_path = uploads_path
        self.results = {
            "metadata": {
                "script": "validate_real_metrics.py",
                "version": "1.0.0",
                "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "python_version": "3.8+",
                "scikit_image_available": HAS_SKIMAGE
            },
            "test_summary": {
                "total_image_pairs": 0,
                "images_processed": 0,
                "errors": 0
            },
            "image_pairs": [],
            "metrics": {
                "compression_ratios": [],
                "ssim_scores": [],
                "psnr_scores": [],
                "processing_times_ms": [],
                "original_sizes_kb": [],
                "compressed_sizes_kb": [],
                "size_reductions_kb": []
            },
            "summary_statistics": {}
        }
    
    def scan_images(self):
        """
        Find all original/compressed image pairs in uploads folder
        """
        print(f"📁 Scanning {self.uploads_path} for image pairs...")
        
        if not os.path.exists(self.uploads_path):
            print(f"❌ ERROR: {self.uploads_path} folder not found!")
            return [], []
        
        originals = sorted([
            f for f in os.listdir(self.uploads_path) 
            if f.startswith("original_")
        ])
        
        compressed = sorted([
            f for f in os.listdir(self.uploads_path) 
            if f.startswith("compressed_")
        ])
        
        print(f"✅ Found {len(originals)} original images")
        print(f"✅ Found {len(compressed)} compressed images")
        
        self.results["test_summary"]["total_image_pairs"] = len(originals)
        
        return originals, compressed
    
    def calculate_basic_metrics(self, orig_img_array, comp_img_array):
        """
        Calculate basic quality metrics using NumPy
        """
        # Flatten to 1D for comparison
        orig_flat = orig_img_array.flatten().astype(float)
        comp_flat = comp_img_array.flatten().astype(float)
        
        # Mean Squared Error
        mse = np.mean((orig_flat - comp_flat) ** 2)
        
        # PSNR approximation (basic, not exact)
        if mse > 0:
            psnr_approx = 10 * np.log10(255 ** 2 / mse)
        else:
            psnr_approx = 100
        
        return psnr_approx
    
    def calculate_metrics(self, original_path, compressed_path):
        """
        Calculate compression metrics for image pair
        """
        start_time = time.time()
        
        try:
            # File sizes
            orig_size = os.path.getsize(original_path)
            comp_size = os.path.getsize(compressed_path)
            compression_ratio = ((orig_size - comp_size) / orig_size) * 100
            
            # Load images
            orig_img = Image.open(original_path).convert('RGB')
            comp_img = Image.open(compressed_path).convert('RGB')
            
            # Resize if needed
            if orig_img.size != comp_img.size:
                comp_img = comp_img.resize(orig_img.size, Image.Resampling.LANCZOS)
            
            # Convert to arrays
            orig_array = np.array(orig_img, dtype=np.float32)
            comp_array = np.array(comp_img, dtype=np.float32)
            
            # Calculate SSIM and PSNR
            if HAS_SKIMAGE:
                ssim_result = ssim(orig_array, comp_array, channel_axis=2, data_range=255)
                ssim_score = ssim_result if isinstance(ssim_result, (int, float)) else ssim_result[0]
                psnr_score = psnr(orig_array, comp_array, data_range=255)
            else:
                ssim_score = 0.0  # Not available
                psnr_score = self.calculate_basic_metrics(orig_array, comp_array)
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            metrics = {
                "compression_ratio_percent": round(compression_ratio, 2),
                "original_size_kb": round(orig_size / 1024, 2),
                "compressed_size_kb": round(comp_size / 1024, 2),
                "size_reduction_kb": round((orig_size - comp_size) / 1024, 2),
                "ssim_score": round(float(ssim_score), 4) if ssim_score else 0.0,
                "psnr_db": round(float(psnr_score), 2),
                "processing_time_ms": round(processing_time, 2)
            }
            
            return metrics, None
        
        except Exception as e:
            return None, str(e)
    
    def validate_all(self):
        """
        Run validation on all image pairs
        """
        print("\n" + "="*60)
        print("🔍 VALIDATING K2SHBWI COMPRESSION METRICS")
        print("="*60 + "\n")
        
        originals, compressed = self.scan_images()
        
        if len(originals) == 0:
            print("❌ No images found to validate!")
            return self.results
        
        print(f"\n📊 Processing {len(originals)} image pairs...\n")
        
        for i, (orig, comp) in enumerate(zip(originals, compressed)):
            orig_path = os.path.join(self.uploads_path, orig)
            comp_path = os.path.join(self.uploads_path, comp)
            
            print(f"[{i+1}/{len(originals)}] Processing: {orig[:50]}...")
            
            metrics, error = self.calculate_metrics(orig_path, comp_path)
            
            if error or metrics is None:
                print(f"    ❌ Error: {error}")
                self.results["test_summary"]["errors"] += 1
            else:
                print(f"    ✅ Compression: {metrics['compression_ratio_percent']}%")
                print(f"       SSIM: {metrics['ssim_score']}, PSNR: {metrics['psnr_db']} dB")
                
                self.results["image_pairs"].append({
                    "original_file": orig,
                    "compressed_file": comp,
                    "metrics": metrics
                })
                
                # Collect statistics
                self.results["metrics"]["compression_ratios"].append(
                    metrics["compression_ratio_percent"]
                )
                self.results["metrics"]["ssim_scores"].append(metrics["ssim_score"])
                self.results["metrics"]["psnr_scores"].append(metrics["psnr_db"])
                self.results["metrics"]["processing_times_ms"].append(
                    metrics["processing_time_ms"]
                )
                self.results["metrics"]["original_sizes_kb"].append(
                    metrics["original_size_kb"]
                )
                self.results["metrics"]["compressed_sizes_kb"].append(
                    metrics["compressed_size_kb"]
                )
                self.results["metrics"]["size_reductions_kb"].append(
                    metrics["size_reduction_kb"]
                )
                
                self.results["test_summary"]["images_processed"] += 1
        
        # Calculate summary statistics
        self._calculate_summary()
        
        return self.results
    
    def _calculate_summary(self):
        """
        Calculate summary statistics from all tests
        """
        metrics = self.results["metrics"]
        
        if len(metrics["compression_ratios"]) == 0:
            return
        
        summary = {
            "test_date": self.results["metadata"]["test_date"],
            "total_images_tested": len(metrics["compression_ratios"]),
            "images_processed_successfully": self.results["test_summary"]["images_processed"],
            "errors": self.results["test_summary"]["errors"],
            "compression": {
                "average_percent": round(np.mean(metrics["compression_ratios"]), 2),
                "min_percent": round(np.min(metrics["compression_ratios"]), 2),
                "max_percent": round(np.max(metrics["compression_ratios"]), 2),
                "std_dev": round(np.std(metrics["compression_ratios"]), 2)
            },
            "quality_ssim": {
                "average": round(np.mean(metrics["ssim_scores"]), 4),
                "min": round(np.min(metrics["ssim_scores"]), 4),
                "max": round(np.max(metrics["ssim_scores"]), 4),
                "std_dev": round(np.std(metrics["ssim_scores"]), 4)
            },
            "quality_psnr": {
                "average_db": round(np.mean(metrics["psnr_scores"]), 2),
                "min_db": round(np.min(metrics["psnr_scores"]), 2),
                "max_db": round(np.max(metrics["psnr_scores"]), 2),
                "std_dev_db": round(np.std(metrics["psnr_scores"]), 2)
            },
            "processing": {
                "total_time_ms": round(np.sum(metrics["processing_times_ms"]), 2),
                "average_per_image_ms": 
                    round(np.mean(metrics["processing_times_ms"]), 2),
                "total_time_seconds": 
                    round(np.sum(metrics["processing_times_ms"]) / 1000, 2)
            },
            "file_sizes": {
                "total_original_kb": round(np.sum(metrics["original_sizes_kb"]), 2),
                "total_compressed_kb": round(np.sum(metrics["compressed_sizes_kb"]), 2),
                "total_reduction_kb": round(np.sum(metrics["size_reductions_kb"]), 2),
                "average_original_per_image_kb": 
                    round(np.mean(metrics["original_sizes_kb"]), 2),
                "average_compressed_per_image_kb": 
                    round(np.mean(metrics["compressed_sizes_kb"]), 2)
            }
        }
        
        self.results["summary_statistics"] = summary
    
    def save_results(self, output_file="validation_results.json"):
        """
        Save validation results to JSON file
        """
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
    
    def print_summary(self):
        """
        Print human-readable summary
        """
        if not self.results["summary_statistics"]:
            print("❌ No results to summarize")
            return
        
        summary = self.results["summary_statistics"]
        
        print("\n" + "="*60)
        print("📈 VALIDATION SUMMARY REPORT")
        print("="*60)
        
        print(f"\nTest Date: {summary['test_date']}")
        print(f"Images Tested: {summary['total_images_tested']}")
        print(f"Successfully Processed: {summary['images_processed_successfully']}")
        print(f"Errors: {summary['errors']}")
        
        print("\n--- COMPRESSION RESULTS ---")
        print(f"Average Compression: {summary['compression']['average_percent']}%")
        print(f"  Min: {summary['compression']['min_percent']}%")
        print(f"  Max: {summary['compression']['max_percent']}%")
        print(f"  Std Dev: {summary['compression']['std_dev']}%")
        
        print("\n--- QUALITY (SSIM) ---")
        print(f"Average SSIM: {summary['quality_ssim']['average']}")
        print(f"  Min: {summary['quality_ssim']['min']}")
        print(f"  Max: {summary['quality_ssim']['max']}")
        print(f"  Std Dev: {summary['quality_ssim']['std_dev']}")
        
        print("\n--- QUALITY (PSNR) ---")
        print(f"Average PSNR: {summary['quality_psnr']['average_db']} dB")
        print(f"  Min: {summary['quality_psnr']['min_db']} dB")
        print(f"  Max: {summary['quality_psnr']['max_db']} dB")
        print(f"  Std Dev: {summary['quality_psnr']['std_dev_db']} dB")
        
        print("\n--- PROCESSING TIME ---")
        print(f"Total Time: {summary['processing']['total_time_seconds']} seconds")
        print(f"Average Per Image: {summary['processing']['average_per_image_ms']} ms")
        
        print("\n--- FILE SIZES ---")
        print(f"Total Original: {summary['file_sizes']['total_original_kb']} KB")
        print(f"Total Compressed: {summary['file_sizes']['total_compressed_kb']} KB")
        print(f"Total Reduction: {summary['file_sizes']['total_reduction_kb']} KB")
        
        print("\n" + "="*60)
        print("✅ VALIDATION COMPLETE")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Create validator
    validator = MetricsValidator()
    
    # Run validation
    results = validator.validate_all()
    
    # Print summary
    validator.print_summary()
    
    # Save results
    validator.save_results("validation_results.json")
    
    print("📊 Next steps:")
    print("  1. Review validation_results.json")
    print("  2. Compare ACTUAL metrics with CLAIMED metrics")
    print("  3. Update format articles with verified data")
    print("  4. Create VALIDATION_REPORT.md")
    print("  5. Add 'VERIFIED' badges to all format pages")
