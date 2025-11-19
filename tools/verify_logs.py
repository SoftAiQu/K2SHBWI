#!/usr/bin/env python3
"""
K2SHBWI Log Verification Tool
Verifies log integrity, detects anomalies, and generates verification reports.

Features:
  - SHA256 hash verification for all logs
  - Data consistency checking
  - Anomaly detection (outliers, missing data)
  - Integrity report generation
  - JSON/TXT report export
  - Real-time verification status

Usage:
  python tools/verify_logs.py --verify all          # Verify all logs
  python tools/verify_logs.py --verify hashes       # Verify hashes only
  python tools/verify_logs.py --verify consistency  # Check consistency
  python tools/verify_logs.py --detect anomalies    # Detect anomalies
  python tools/verify_logs.py --report              # Generate report
  python tools/verify_logs.py --full                # Full verification
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class LogVerifier:
    """Verify K2SHBWI logs for integrity and anomalies"""
    
    def __init__(self):
        """Initialize log verifier"""
        self.base_logs_dir = Path(__file__).parent.parent / "logs"
        self.benchmark_dir = self.base_logs_dir / "benchmark_results"
        self.cli_dir = self.base_logs_dir / "cli_runs"
        self.test_dir = self.base_logs_dir / "test_runs"
        
        self.verification_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_files': 0,
            'hash_checks': {'passed': 0, 'failed': 0, 'missing': 0},
            'consistency_checks': {'passed': 0, 'failed': 0},
            'anomaly_checks': {'found': 0, 'details': []},
            'issues': [],
            'warnings': [],
            'summary': {}
        }
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_hashes(self) -> Dict[str, Any]:
        """Verify SHA256 hashes for all logs"""
        results = {'verified': [], 'failed': [], 'missing_hash': []}
        
        for log_dir in [self.benchmark_dir, self.cli_dir, self.test_dir]:
            if not log_dir.exists():
                continue
            
            json_files = list(log_dir.glob("*.json"))
            
            for json_file in json_files:
                hash_file = log_dir / f"{json_file.stem}.sha256"
                
                if not hash_file.exists():
                    results['missing_hash'].append(str(json_file.name))
                    self.verification_results['hash_checks']['missing'] += 1
                    self.verification_results['warnings'].append(
                        f"Missing hash file for {json_file.name}"
                    )
                    continue
                
                # Read stored hash
                try:
                    with open(hash_file, 'r') as f:
                        stored_hash = f.read().strip().split()[0]
                except Exception as e:
                    results['missing_hash'].append(str(json_file.name))
                    self.verification_results['issues'].append(
                        f"Error reading hash file {hash_file.name}: {e}"
                    )
                    continue
                
                # Calculate actual hash
                try:
                    actual_hash = self.calculate_hash(json_file)
                    
                    if stored_hash == actual_hash:
                        results['verified'].append(str(json_file.name))
                        self.verification_results['hash_checks']['passed'] += 1
                    else:
                        results['failed'].append({
                            'file': str(json_file.name),
                            'expected': stored_hash,
                            'actual': actual_hash
                        })
                        self.verification_results['hash_checks']['failed'] += 1
                        self.verification_results['issues'].append(
                            f"Hash mismatch for {json_file.name}"
                        )
                except Exception as e:
                    results['failed'].append({
                        'file': str(json_file.name),
                        'error': str(e)
                    })
                    self.verification_results['hash_checks']['failed'] += 1
                    self.verification_results['issues'].append(
                        f"Error hashing {json_file.name}: {e}"
                    )
        
        return results
    
    def check_consistency(self) -> Dict[str, Any]:
        """Check data consistency across logs"""
        consistency_issues = []
        
        # Load all JSON logs
        all_logs = []
        for log_dir in [self.benchmark_dir, self.cli_dir, self.test_dir]:
            if not log_dir.exists():
                continue
            
            for json_file in log_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        log_data = json.load(f)
                        all_logs.append((json_file.name, log_data))
                except Exception as e:
                    consistency_issues.append({
                        'type': 'JSON_PARSE_ERROR',
                        'file': json_file.name,
                        'error': str(e)
                    })
                    self.verification_results['consistency_checks']['failed'] += 1
                    continue
        
        # Check each log for required fields
        required_fields = ['timestamp', 'logger_name', 'log_type', 'metrics', 'summary']
        
        for file_name, log_data in all_logs:
            missing_fields = [field for field in required_fields if field not in log_data]
            
            if missing_fields:
                consistency_issues.append({
                    'type': 'MISSING_FIELDS',
                    'file': file_name,
                    'missing': missing_fields
                })
                self.verification_results['consistency_checks']['failed'] += 1
            else:
                # Check metrics structure
                if not isinstance(log_data['metrics'], list):
                    consistency_issues.append({
                        'type': 'INVALID_METRICS_TYPE',
                        'file': file_name,
                        'expected': 'list',
                        'actual': type(log_data['metrics']).__name__
                    })
                    self.verification_results['consistency_checks']['failed'] += 1
                else:
                    # Validate each metric
                    for idx, metric in enumerate(log_data['metrics']):
                        if 'type' not in metric:
                            consistency_issues.append({
                                'type': 'METRIC_MISSING_TYPE',
                                'file': file_name,
                                'metric_index': idx
                            })
                            self.verification_results['consistency_checks']['failed'] += 1
                    
                    self.verification_results['consistency_checks']['passed'] += 1
        
        return {'issues': consistency_issues, 'total_logs_checked': len(all_logs)}
    
    def detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in logs (outliers, suspicious values)"""
        anomalies = []
        
        # Collect all compression metrics
        compression_ratios = []
        processing_times = []
        
        for log_dir in [self.benchmark_dir, self.cli_dir, self.test_dir]:
            if not log_dir.exists():
                continue
            
            for json_file in log_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        log_data = json.load(f)
                        
                        for metric in log_data.get('metrics', []):
                            # Compression ratio analysis
                            if metric.get('type') == 'compression':
                                ratio = metric.get('compression_ratio_percent', 0)
                                compression_ratios.append({
                                    'value': ratio,
                                    'file': json_file.name,
                                    'metric_index': len(compression_ratios)
                                })
                                
                                # Flag suspicious compression ratios
                                if ratio > 100:
                                    anomalies.append({
                                        'type': 'COMPRESSION_RATIO_ANOMALY',
                                        'file': json_file.name,
                                        'reason': f'Compression ratio > 100% ({ratio}%)',
                                        'severity': 'HIGH'
                                    })
                                    self.verification_results['anomaly_checks']['found'] += 1
                                elif ratio < -10:
                                    anomalies.append({
                                        'type': 'NEGATIVE_COMPRESSION_ANOMALY',
                                        'file': json_file.name,
                                        'reason': f'Compression ratio < -10% ({ratio}%)',
                                        'severity': 'MEDIUM'
                                    })
                                    self.verification_results['anomaly_checks']['found'] += 1
                                
                                # Processing time analysis
                                time = metric.get('processing_time_ms', 0)
                                processing_times.append({
                                    'value': time,
                                    'file': json_file.name
                                })
                                
                                # Flag suspiciously slow operations
                                if time > 5000:  # 5 seconds
                                    anomalies.append({
                                        'type': 'PROCESSING_TIME_ANOMALY',
                                        'file': json_file.name,
                                        'reason': f'Processing time > 5000ms ({time}ms)',
                                        'severity': 'LOW'
                                    })
                                    self.verification_results['anomaly_checks']['found'] += 1
                            
                            # Test status anomaly
                            elif metric.get('type') == 'test':
                                status = metric.get('status', '').upper()
                                if status not in ['PASS', 'FAIL', 'SKIP']:
                                    anomalies.append({
                                        'type': 'INVALID_TEST_STATUS',
                                        'file': json_file.name,
                                        'invalid_status': status,
                                        'severity': 'HIGH'
                                    })
                                    self.verification_results['anomaly_checks']['found'] += 1
                            
                            # SSIM score anomaly
                            elif metric.get('type') == 'ssim':
                                score = metric.get('ssim_score', 0)
                                if score < 0 or score > 1:
                                    anomalies.append({
                                        'type': 'SSIM_SCORE_ANOMALY',
                                        'file': json_file.name,
                                        'invalid_score': score,
                                        'reason': 'SSIM score must be between 0 and 1',
                                        'severity': 'HIGH'
                                    })
                                    self.verification_results['anomaly_checks']['found'] += 1
                
                except Exception as e:
                    pass  # Already caught in consistency check
        
        # Statistical anomaly detection for compression ratios
        if len(compression_ratios) > 5:
            ratios = [m['value'] for m in compression_ratios]
            mean_ratio = sum(ratios) / len(ratios)
            variance = sum((x - mean_ratio) ** 2 for x in ratios) / len(ratios)
            std_dev = variance ** 0.5
            
            # Flag values more than 2 standard deviations from mean
            for item in compression_ratios:
                if abs(item['value'] - mean_ratio) > 2 * std_dev:
                    anomalies.append({
                        'type': 'STATISTICAL_OUTLIER',
                        'file': item['file'],
                        'value': item['value'],
                        'mean': round(mean_ratio, 2),
                        'std_dev': round(std_dev, 2),
                        'severity': 'LOW'
                    })
        
        self.verification_results['anomaly_checks']['details'] = anomalies
        
        return {
            'anomalies_found': len(anomalies),
            'anomalies': anomalies,
            'compression_stats': self._calculate_stats(compression_ratios),
            'processing_time_stats': self._calculate_stats(processing_times)
        }
    
    def _calculate_stats(self, values: List[Dict]) -> Dict:
        """Calculate statistics for a list of values"""
        if not values:
            return {}
        
        nums = [v['value'] for v in values]
        return {
            'count': len(nums),
            'mean': round(sum(nums) / len(nums), 2),
            'min': round(min(nums), 2),
            'max': round(max(nums), 2),
            'median': round(sorted(nums)[len(nums) // 2], 2)
        }
    
    def verify_all(self) -> Dict[str, Any]:
        """Run all verification checks"""
        click.echo("\n" + "="*80)
        click.echo("K2SHBWI LOG VERIFICATION")
        click.echo("="*80)
        
        click.echo("\n[1/3] Verifying SHA256 hashes...")
        hash_results = self.verify_hashes()
        
        click.echo(f"  ✓ Verified: {self.verification_results['hash_checks']['passed']}")
        click.echo(f"  ✗ Failed: {self.verification_results['hash_checks']['failed']}")
        click.echo(f"  ⚠ Missing: {self.verification_results['hash_checks']['missing']}")
        
        click.echo("\n[2/3] Checking data consistency...")
        consistency_results = self.check_consistency()
        click.echo(f"  ✓ Passed: {self.verification_results['consistency_checks']['passed']}")
        click.echo(f"  ✗ Failed: {self.verification_results['consistency_checks']['failed']}")
        
        click.echo("\n[3/3] Detecting anomalies...")
        anomaly_results = self.detect_anomalies()
        click.echo(f"  ⚠ Anomalies found: {anomaly_results['anomalies_found']}")
        
        # Summary
        self.verification_results['hash_results'] = hash_results
        self.verification_results['consistency_results'] = consistency_results
        self.verification_results['anomaly_results'] = anomaly_results
        
        total_issues = (
            self.verification_results['hash_checks']['failed'] +
            self.verification_results['consistency_checks']['failed'] +
            anomaly_results['anomalies_found']
        )
        
        if total_issues == 0:
            click.echo("\n" + "="*80)
            click.echo("✅ VERIFICATION PASSED - All checks successful!")
            click.echo("="*80 + "\n")
        else:
            click.echo("\n" + "="*80)
            click.echo(f"⚠️  VERIFICATION ISSUES FOUND: {total_issues}")
            click.echo("="*80 + "\n")
        
        return self.verification_results
    
    def export_report_json(self, output_file: Optional[str] = None) -> str:
        """Export verification report as JSON"""
        if not output_file:
            output_file = str(self.base_logs_dir / "VERIFICATION_REPORT.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.verification_results, f, indent=2)
        
        return str(output_file)
    
    def export_report_txt(self, output_file: Optional[str] = None) -> str:
        """Export verification report as TXT"""
        if not output_file:
            output_file = str(self.base_logs_dir / "VERIFICATION_REPORT.txt")
        
        results = self.verification_results
        
        txt_content = f"""
================================================================================
K2SHBWI LOG VERIFICATION REPORT
================================================================================

Generated: {results['timestamp']}
Report Location: {self.base_logs_dir}

================================================================================
HASH VERIFICATION
================================================================================

Verified:     {results['hash_checks']['passed']}
Failed:       {results['hash_checks']['failed']}
Missing:      {results['hash_checks']['missing']}

Status: {'✅ PASSED' if results['hash_checks']['failed'] == 0 else '❌ FAILED'}

"""
        
        if results.get('hash_results', {}).get('failed'):
            txt_content += "Failed Hash Checks:\n"
            for failure in results['hash_results']['failed']:
                txt_content += f"  • {failure.get('file', 'Unknown')}\n"
            txt_content += "\n"
        
        txt_content += f"""
================================================================================
CONSISTENCY CHECKS
================================================================================

Passed:       {results['consistency_checks']['passed']}
Failed:       {results['consistency_checks']['failed']}

Status: {'✅ PASSED' if results['consistency_checks']['failed'] == 0 else '❌ FAILED'}

"""
        
        if results.get('consistency_results', {}).get('issues'):
            txt_content += "Consistency Issues:\n"
            for issue in results['consistency_results']['issues']:
                txt_content += f"  • {issue.get('type', 'Unknown')}: {issue.get('file', 'Unknown')}\n"
            txt_content += "\n"
        
        txt_content += f"""
================================================================================
ANOMALY DETECTION
================================================================================

Anomalies Found: {results['anomaly_checks']['found']}

Status: {'✅ NO ANOMALIES' if results['anomaly_checks']['found'] == 0 else '⚠️ ANOMALIES DETECTED'}

"""
        
        if results.get('anomaly_results', {}).get('anomalies'):
            txt_content += "Detected Anomalies:\n"
            for anomaly in results['anomaly_results']['anomalies'][:10]:  # Show first 10
                txt_content += f"  • {anomaly.get('type', 'Unknown')} [{anomaly.get('severity', 'INFO')}]\n"
                txt_content += f"    File: {anomaly.get('file', 'Unknown')}\n"
                txt_content += f"    Reason: {anomaly.get('reason', anomaly.get('invalid_score', anomaly.get('invalid_status', 'N/A')))}\n"
            txt_content += "\n"
        
        if results.get('issues'):
            txt_content += f"""
================================================================================
CRITICAL ISSUES
================================================================================

"""
            for issue in results['issues']:
                txt_content += f"  ❌ {issue}\n"
            txt_content += "\n"
        
        if results.get('warnings'):
            txt_content += f"""
================================================================================
WARNINGS
================================================================================

"""
            for warning in results['warnings']:
                txt_content += f"  ⚠️  {warning}\n"
            txt_content += "\n"
        
        txt_content += f"""
================================================================================
SUMMARY
================================================================================

Total Logs Verified: {results['hash_checks']['passed'] + results['hash_checks']['failed'] + results['hash_checks']['missing']}
Hash Verification: {'✅ PASSED' if results['hash_checks']['failed'] == 0 else '❌ FAILED'}
Consistency Check: {'✅ PASSED' if results['consistency_checks']['failed'] == 0 else '❌ FAILED'}
Anomaly Detection: {'✅ CLEAN' if results['anomaly_checks']['found'] == 0 else f"⚠️ {results['anomaly_checks']['found']} ANOMALIES"}

Overall Status: {'✅ VERIFICATION PASSED' if (results['hash_checks']['failed'] == 0 and results['consistency_checks']['failed'] == 0 and results['anomaly_checks']['found'] == 0) else '❌ VERIFICATION FAILED'}

================================================================================
END OF REPORT
================================================================================

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return str(output_file)


# ============================================================================
# CLI INTERFACE
# ============================================================================

@click.group()
def cli():
    """K2SHBWI Log Verification Tool - Verify log integrity and detect anomalies"""
    pass


@cli.command()
@click.option('--type', 'verify_type', type=click.Choice(['all', 'hashes', 'consistency', 'anomalies']), 
              default='all', help='Type of verification to perform')
def verify(verify_type):
    """Verify logs"""
    verifier = LogVerifier()
    
    if verify_type == 'all':
        verifier.verify_all()
    elif verify_type == 'hashes':
        click.echo("\nVerifying SHA256 hashes...\n")
        results = verifier.verify_hashes()
        click.echo(f"✓ Verified: {len(results['verified'])}")
        click.echo(f"✗ Failed: {len(results['failed'])}")
        click.echo(f"⚠ Missing: {len(results['missing_hash'])}")
    elif verify_type == 'consistency':
        click.echo("\nChecking data consistency...\n")
        results = verifier.check_consistency()
        click.echo(f"Issues Found: {len(results['issues'])}")
        for issue in results['issues'][:5]:
            click.echo(f"  • {issue.get('type')}: {issue.get('file')}")
    elif verify_type == 'anomalies':
        click.echo("\nDetecting anomalies...\n")
        results = verifier.detect_anomalies()
        click.echo(f"Anomalies Found: {results['anomalies_found']}")
        for anomaly in results['anomalies'][:5]:
            click.echo(f"  • {anomaly.get('type')}: {anomaly.get('file')}")


@cli.command()
def report():
    """Generate verification report"""
    verifier = LogVerifier()
    verifier.verify_all()
    
    json_file = verifier.export_report_json()
    txt_file = verifier.export_report_txt()
    
    click.echo(f"\n✅ JSON Report: {json_file}")
    click.echo(f"✅ TXT Report: {txt_file}\n")


if __name__ == '__main__':
    cli()
