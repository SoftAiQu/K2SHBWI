#!/usr/bin/env python3
"""
Comprehensive Test Suite for K2SHBWI Click CLI Migration
Tests all phases: Commands, Converters, Viewers, Testing, Documentation

Now with real-time logging:
  - Metrics logged to /logs/test_runs/
  - JSON, TXT, and hash files generated
  - Test status, timings, and file sizes recorded
"""

import subprocess
import json
from pathlib import Path
import sys
import time
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Go up one level from /tests to root

from src.utils.test_logger import TestLogger

class TestRunner:
    """Run comprehensive tests for all phases"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
        self.python_exe = 'python'  # Use system Python
        self.cli = "tools\\cli_click.py"

        # Initialize logger
        self.logger = TestLogger(logger_name="comprehensive_test_suite", log_type="test")
    
    def run_command(self, *args):
        """Run CLI command and capture output"""
        try:
            cmd = [self.python_exe, self.cli] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def test(self, name, test_func):
        """Run a test"""
        print(f"\nTesting: {name}...", end=" ")
        test_start_time = time.time()
        
        try:
            test_func()
            elapsed_ms = (time.time() - test_start_time) * 1000
            print("[PASS]")
            self.test_results.append({"name": name, "status": "PASS"})
            self.passed += 1
            
            # Log test result
            self.logger.log_test_result(
                test_name=name,
                status="PASS",
                input_bytes=0,
                output_bytes=0,
                processing_time_ms=elapsed_ms,
                compression_type="N/A",
                error_msg=None
            )
        except AssertionError as e:
            elapsed_ms = (time.time() - test_start_time) * 1000
            print(f"[FAIL]: {e}")
            self.test_results.append({"name": name, "status": "FAIL", "error": str(e)})
            self.failed += 1
            
            # Log test result
            self.logger.log_test_result(
                test_name=name,
                status="FAIL",
                input_bytes=0,
                output_bytes=0,
                processing_time_ms=elapsed_ms,
                compression_type="N/A",
                error_msg=str(e)
            )
        except Exception as e:
            elapsed_ms = (time.time() - test_start_time) * 1000
            print(f"[ERROR]: {e}")
            self.test_results.append({"name": name, "status": "ERROR", "error": str(e)})
            self.failed += 1
            
            # Log test result
            self.logger.log_test_result(
                test_name=name,
                status="FAIL",
                input_bytes=0,
                output_bytes=0,
                processing_time_ms=elapsed_ms,
                compression_type="N/A",
                error_msg=str(e)
            )
    
    # PHASE 3 Tests
    def test_create_command(self):
        """Test create command"""
        code, out, err = self.run_command("create", "-i", "test_image.png", "-o", "test_p3_create.k2sh")
        assert code == 0, f"Exit code {code}: {err}"
        assert "[OK]" in out or "Created:" in out, f"Unexpected output: {out}"
        assert Path("test_p3_create.k2sh").exists(), "Output file not created"
    
    def test_create_with_metadata(self):
        """Test create with metadata"""
        # Create with metadata flags directly
        code, out, err = self.run_command("create", "-i", "test_image.png", "-o", "test_p3_meta.k2sh", "-t", "TestTitle")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p3_meta.k2sh").exists(), "Output file not created"
    
    def test_info_command(self):
        """Test info command"""
        code, out, err = self.run_command("info", "test_output_click.k2sh")
        assert code == 0, f"Exit code {code}: {err}"
        assert "File Information" in out, "Missing title in output"
    
    def test_validate_command(self):
        """Test validate command"""
        code, out, err = self.run_command("validate", "test_output_click.k2sh")
        assert code == 0, f"Exit code {code}: {err}"
        assert "[OK]" in out and "VALID" in out, "File validation failed"
    
    def test_decode_command(self):
        """Test decode command"""
        code, out, err = self.run_command("decode", "test_output_click.k2sh", "-o", "test_p3_decoded.png")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p3_decoded.png").exists(), "Decoded image not created"
        assert "[OK]" in out, "Decode incomplete"
    
    def test_batch_command(self):
        """Test batch command"""
        # Use existing batch_input directory
        code, out, err = self.run_command("batch", "-i", "batch_input", "-o", "test_p3_batch")
        assert code == 0, f"Exit code {code}: {err}"
        assert "Successful:" in out, "Batch processing failed"
        assert "3" in out, "All files should succeed"
    
    def test_encode_command(self):
        """Test encode command"""
        code, out, err = self.run_command("encode", "-i", "test_image.png", "-o", "test_p3_encode.k2sh")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p3_encode.k2sh").exists(), "Encoded file not created"
    
    # PHASE 4 Tests
    def test_convert_html(self):
        """Test HTML conversion"""
        code, out, err = self.run_command("convert", "test_output_click.k2sh", "-f", "html", "-o", "test_p4_convert.html")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p4_convert.html").exists(), "HTML file not created"
        assert Path("test_p4_convert.html").stat().st_size > 0, "HTML file is empty"
        
        # Check HTML content
        html_content = Path("test_p4_convert.html").read_text()
        assert "<html" in html_content.lower(), "Not valid HTML"
    
    def test_convert_pdf(self):
        """Test PDF conversion"""
        code, out, err = self.run_command("convert", "test_output_click.k2sh", "-f", "pdf", "-o", "test_p4_convert.pdf")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p4_convert.pdf").exists(), "PDF file not created"
        assert Path("test_p4_convert.pdf").stat().st_size > 0, "PDF file is empty"
    
    def test_convert_pptx(self):
        """Test PPTX conversion"""
        code, out, err = self.run_command("convert", "test_output_click.k2sh", "-f", "pptx", "-o", "test_p4_convert.pptx")
        assert code == 0, f"Exit code {code}: {err}"
        assert Path("test_p4_convert.pptx").exists(), "PPTX file not created"
        assert Path("test_p4_convert.pptx").stat().st_size > 0, "PPTX file is empty"
    
    def test_convert_all_formats(self):
        """Test all conversion formats"""
        for fmt in ['html', 'pdf', 'pptx']:
            code, out, err = self.run_command("convert", "test_output_click.k2sh", "-f", fmt, "-o", f"test_all_{fmt}.{fmt}")
            assert code == 0, f"Conversion to {fmt} failed: {err}"
            output_file = f"test_all_{fmt}.{fmt}"
            assert Path(output_file).exists(), f"{fmt} file not created"
    
    # PHASE 5 Tests
    def test_view_help(self):
        """Test view command help"""
        code, out, err = self.run_command("view", "--help")
        assert code == 0, f"Exit code {code}: {err}"
        assert "web" in out.lower(), "Web viewer not mentioned"
        assert "desktop" in out.lower(), "Desktop viewer not mentioned"
    
    # PHASE 6 Tests
    def test_all_commands_have_help(self):
        """Test that all commands have help text"""
        commands = ["create", "info", "validate", "batch", "encode", "decode", "convert", "view"]
        for cmd in commands:
            code, out, err = self.run_command(cmd, "--help")
            assert code == 0, f"Help not available for {cmd}"
            assert "Usage:" in out, f"No usage for {cmd}"
    
    def test_create_multiple_files(self):
        """Test creating multiple K2SHBWI files"""
        for i in range(3):
            code, out, err = self.run_command("create", "-i", "test_image.png", "-o", f"test_multi_{i}.k2sh")
            assert code == 0, f"Failed to create file {i}: {err}"
            assert Path(f"test_multi_{i}.k2sh").exists(), f"File test_multi_{i}.k2sh not created"
    
    def test_validate_all_outputs(self):
        """Test validation of all created files"""
        test_files = list(Path(".").glob("test_p*_*.k2sh")) + list(Path(".").glob("test_multi_*.k2sh"))
        for file in test_files[:5]:  # Test first 5
            code, out, err = self.run_command("validate", str(file))
            assert code == 0, f"Validation failed for {file}"
    
    def test_verbose_output(self):
        """Test verbose output flag"""
        code, out, err = self.run_command("info", "test_output_click.k2sh", "-v")
        assert code == 0, f"Exit code {code}: {err}"
        # Verbose output should have more info
        assert len(out) > 100, "Verbose output seems truncated"
    
    # PHASE 7 Tests (Documentation)
    def test_cli_version(self):
        """Test CLI version display"""
        code, out, err = self.run_command("--version")
        assert code == 0, f"Exit code {code}: {err}"
        assert "1.0.0" in out, "Version not displayed correctly"
    
    def test_cli_main_help(self):
        """Test main help command"""
        code, out, err = self.run_command("--help")
        assert code == 0, f"Exit code {code}: {err}"
        assert "Interactive Image Encoding" in out or "K2SHBWI" in out, "Main help not descriptive"
    
    def test_command_examples(self):
        """Test that command help includes examples"""
        code, out, err = self.run_command("create", "--help")
        assert code == 0, f"Exit code {code}: {err}"
        # Some commands should have examples
        has_example = "example" in out.lower() or "k2shbwi" in out.lower()
        assert has_example, "Command help should include examples or usage"
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("K2SHBWI CLICK CLI - COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        # PHASE 3 Tests
        print("\n[PHASE 3] Implement 8 Commands")
        self.test("Create Command", self.test_create_command)
        self.test("Create with Metadata", self.test_create_with_metadata)
        self.test("Info Command", self.test_info_command)
        self.test("Validate Command", self.test_validate_command)
        self.test("Decode Command", self.test_decode_command)
        self.test("Batch Command", self.test_batch_command)
        self.test("Encode Command", self.test_encode_command)
        
        # PHASE 4 Tests
        print("\n[PHASE 4] Create Converter Modules")
        self.test("Convert to HTML", self.test_convert_html)
        self.test("Convert to PDF", self.test_convert_pdf)
        self.test("Convert to PPTX", self.test_convert_pptx)
        self.test("All Conversion Formats", self.test_convert_all_formats)
        
        # PHASE 5 Tests
        print("\n[PHASE 5] Create Viewer Modules")
        self.test("View Command Help", self.test_view_help)
        
        # PHASE 6 Tests
        print("\n[PHASE 6] Testing & Validation")
        self.test("All Commands Have Help", self.test_all_commands_have_help)
        self.test("Create Multiple Files", self.test_create_multiple_files)
        self.test("Validate All Outputs", self.test_validate_all_outputs)
        self.test("Verbose Output", self.test_verbose_output)
        
        # PHASE 7 Tests
        print("\n[PHASE 7] Documentation")
        self.test("CLI Version Display", self.test_cli_version)
        self.test("Main Help", self.test_cli_main_help)
        self.test("Command Examples", self.test_command_examples)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"[PASS] Passed:  {self.passed}")
        print(f"[FAIL] Failed:  {self.failed}")
        print(f"[TIME] Time:    {elapsed:.2f}s")
        print(f"[INFO] Total:   {self.passed + self.failed}")
        
        if self.failed == 0:
            print("\n*** ALL TESTS PASSED! ***")
        else:
            print(f"\n*** {self.failed} tests failed ***")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "[OK]" if result["status"] == "PASS" else "[XX]"
            print(f"{status_icon} {result['name']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        # Save results to file
        with open("TEST_RESULTS.json", "w") as f:
            json.dump({
                "passed": self.passed,
                "failed": self.failed,
                "total": self.passed + self.failed,
                "elapsed_seconds": elapsed,
                "results": self.test_results
            }, f, indent=2)
        
        print("\nFull results saved to TEST_RESULTS.json")
        
        # Save logs with summary
        self.logger.add_summary({
            "test_suite": "comprehensive_test_suite",
            "total_tests": self.passed + self.failed,
            "passed_tests": self.passed,
            "failed_tests": self.failed,
            "total_time_seconds": elapsed,
            "success_rate_percent": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        })
        log_paths = self.logger.save_log()
        
        print(f"\n[Logging] Metrics saved to {log_paths['json']}")
        
        sys.exit(0 if self.failed == 0 else 1)


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
