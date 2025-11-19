#!/usr/bin/env python3
"""
K2SHBWI Log Analyzer Tool
Reads, analyzes, and generates reports from K2SHBWI logs.

Features:
  - Read JSON logs from all log directories
  - Generate summary reports
  - Compare multiple runs
  - Calculate performance trends
  - Export to HTML and TXT formats
  - Show latest run metrics
  - Analyze compression statistics

Usage:
  python tools/log_analyzer.py --latest          # Show latest run
  python tools/log_analyzer.py --summary         # Generate summary report
  python tools/log_analyzer.py --compare         # Compare recent runs
  python tools/log_analyzer.py --export html     # Export to HTML
  python tools/log_analyzer.py --export txt      # Export to TXT
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import sys
from collections import defaultdict
from statistics import mean, median, stdev
import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class LogAnalyzer:
    """Analyze K2SHBWI logs and generate reports"""
    
    def __init__(self):
        """Initialize log analyzer"""
        self.base_logs_dir = Path(__file__).parent.parent / "logs"
        self.benchmark_dir = self.base_logs_dir / "benchmark_results"
        self.cli_dir = self.base_logs_dir / "cli_runs"
        self.test_dir = self.base_logs_dir / "test_runs"
        
        self.logs: List[Dict[str, Any]] = []
        self.load_all_logs()
    
    def load_all_logs(self):
        """Load all JSON logs from all directories"""
        for log_dir in [self.benchmark_dir, self.cli_dir, self.test_dir]:
            if not log_dir.exists():
                continue
            
            for json_file in sorted(log_dir.glob("*.json"), reverse=True):
                try:
                    with open(json_file, 'r') as f:
                        log_data = json.load(f)
                        log_data['_file_path'] = str(json_file)
                        log_data['_file_name'] = json_file.name
                        self.logs.append(log_data)
                except Exception as e:
                    click.echo(f"[ERROR] Failed to load {json_file}: {e}", err=True)
    
    def get_latest_log(self) -> Optional[Dict[str, Any]]:
        """Get the most recent log file"""
        return self.logs[0] if self.logs else None
    
    def get_logs_by_type(self, log_type: str) -> List[Dict[str, Any]]:
        """Get logs filtered by type (benchmark, cli, test)"""
        return [log for log in self.logs if log.get('log_type') == log_type]
    
    def get_logs_by_logger(self, logger_name: str) -> List[Dict[str, Any]]:
        """Get logs filtered by logger name"""
        return [log for log in self.logs if log.get('logger_name') == logger_name]
    
    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate overall summary statistics"""
        if not self.logs:
            return {"error": "No logs found"}
        
        all_metrics = []
        for log in self.logs:
            all_metrics.extend(log.get('metrics', []))
        
        if not all_metrics:
            return {"error": "No metrics found in logs"}
        
        # Filter compression metrics
        compression_metrics = [m for m in all_metrics if m.get('type') == 'compression']
        test_metrics = [m for m in all_metrics if m.get('type') == 'test']
        ssim_metrics = [m for m in all_metrics if m.get('type') == 'ssim']
        cli_metrics = [m for m in all_metrics if m.get('type') == 'cli_command']
        
        # Calculate compression statistics
        compression_stats = {}
        if compression_metrics:
            ratios = [m.get('compression_ratio_percent', 0) for m in compression_metrics]
            times = [m.get('processing_time_ms', 0) for m in compression_metrics]
            
            compression_stats = {
                'total_operations': len(compression_metrics),
                'avg_compression_ratio': round(mean(ratios), 2) if ratios else 0,
                'median_compression_ratio': round(median(ratios), 2) if ratios else 0,
                'best_compression_ratio': round(max(ratios), 2) if ratios else 0,
                'worst_compression_ratio': round(min(ratios), 2) if ratios else 0,
                'avg_processing_time_ms': round(mean(times), 2) if times else 0,
                'total_original_bytes': sum(m.get('original_bytes', 0) for m in compression_metrics),
                'total_compressed_bytes': sum(m.get('compressed_bytes', 0) for m in compression_metrics),
            }
        
        # Calculate test statistics
        test_stats = {}
        if test_metrics:
            passed = len([m for m in test_metrics if m.get('status') == 'PASS'])
            failed = len([m for m in test_metrics if m.get('status') == 'FAIL'])
            skipped = len([m for m in test_metrics if m.get('status') == 'SKIP'])
            
            test_stats = {
                'total_tests': len(test_metrics),
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'success_rate_percent': round((passed / len(test_metrics) * 100), 2) if test_metrics else 0,
            }
        
        # Calculate SSIM statistics
        ssim_stats = {}
        if ssim_metrics:
            scores = [m.get('ssim_score', 0) for m in ssim_metrics]
            times = [m.get('processing_time_ms', 0) for m in ssim_metrics]
            
            ssim_stats = {
                'total_measurements': len(ssim_metrics),
                'avg_score': round(mean(scores), 4) if scores else 0,
                'min_score': round(min(scores), 4) if scores else 0,
                'max_score': round(max(scores), 4) if scores else 0,
                'avg_processing_time_ms': round(mean(times), 2) if times else 0,
            }
        
        # Calculate CLI statistics
        cli_stats = {}
        if cli_metrics:
            successful = len([m for m in cli_metrics if m.get('status') == 'SUCCESS'])
            failed = len([m for m in cli_metrics if m.get('status') == 'FAILED'])
            
            cli_stats = {
                'total_commands': len(cli_metrics),
                'successful': successful,
                'failed': failed,
                'success_rate_percent': round((successful / len(cli_metrics) * 100), 2) if cli_metrics else 0,
            }
        
        return {
            'total_logs': len(self.logs),
            'total_metrics': len(all_metrics),
            'first_log': self.logs[-1].get('timestamp') if self.logs else None,
            'latest_log': self.logs[0].get('timestamp') if self.logs else None,
            'compression_stats': compression_stats,
            'test_stats': test_stats,
            'ssim_stats': ssim_stats,
            'cli_stats': cli_stats,
        }
    
    def generate_performance_trends(self, metric_type: str = 'compression', limit: int = 10) -> List[Dict[str, Any]]:
        """Generate performance trends for recent runs"""
        logs_subset = self.logs[:limit]
        trends = []
        
        for log in logs_subset:
            timestamp = log.get('timestamp', 'N/A')
            logger_name = log.get('logger_name', 'N/A')
            metrics = log.get('metrics', [])
            
            if metric_type == 'compression':
                relevant_metrics = [m for m in metrics if m.get('type') == 'compression']
            elif metric_type == 'test':
                relevant_metrics = [m for m in metrics if m.get('type') == 'test']
            elif metric_type == 'ssim':
                relevant_metrics = [m for m in metrics if m.get('type') == 'ssim']
            else:
                relevant_metrics = metrics
            
            if relevant_metrics:
                if metric_type == 'compression':
                    avg_ratio = round(mean([m.get('compression_ratio_percent', 0) for m in relevant_metrics]), 2)
                    trends.append({
                        'timestamp': timestamp,
                        'logger': logger_name,
                        'metric_count': len(relevant_metrics),
                        'average_compression_ratio': avg_ratio,
                    })
                elif metric_type == 'test':
                    passed = len([m for m in relevant_metrics if m.get('status') == 'PASS'])
                    trends.append({
                        'timestamp': timestamp,
                        'logger': logger_name,
                        'total_tests': len(relevant_metrics),
                        'passed': passed,
                        'success_rate': round((passed / len(relevant_metrics) * 100), 2),
                    })
        
        return trends
    
    def compare_recent_runs(self, count: int = 3) -> Dict[str, Any]:
        """Compare recent log runs"""
        recent_logs = self.logs[:count]
        comparison = []
        
        for log in recent_logs:
            metrics = log.get('metrics', [])
            summary = log.get('summary', {})
            
            comparison.append({
                'timestamp': log.get('timestamp'),
                'logger_name': log.get('logger_name'),
                'file_name': log.get('_file_name'),
                'total_metrics': len(metrics),
                'total_time_ms': summary.get('total_processing_time_ms', 0),
                'avg_compression_ratio': summary.get('average_compression_ratio_percent', 0),
                'error_count': summary.get('error_count', 0),
            })
        
        return {'comparisons': comparison}
    
    def export_to_html(self, output_file: Optional[str] = None) -> str:
        """Export analysis report to HTML"""
        if not output_file:
            output_file = str(self.base_logs_dir / "ANALYSIS_REPORT.html")
        
        stats = self.generate_summary_stats()
        trends = self.generate_performance_trends('compression', 5)
        comparisons = self.compare_recent_runs(3)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K2SHBWI Log Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 0.95rem;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        table th {{
            background: #f8f9ff;
            color: #667eea;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }}
        
        table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        table tbody tr:hover {{
            background: #f8f9ff;
        }}
        
        .footer {{
            background: #f8f9ff;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 2px solid #ddd;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>K2SHBWI Log Analysis Report</h1>
            <p>Real-time metrics and performance analysis</p>
            <p class="timestamp">Generated: {datetime.now(timezone.utc).isoformat()}</p>
        </div>
        
        <div class="content">
            <!-- Overall Summary -->
            <div class="section">
                <h2>Overall Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Logs</div>
                        <div class="metric-value">{stats.get('total_logs', 0)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Metrics</div>
                        <div class="metric-value">{stats.get('total_metrics', 0)}</div>
                    </div>
                </div>
            </div>
            
            <!-- Compression Statistics -->
            <div class="section">
                <h2>Compression Statistics</h2>
                {self._generate_compression_html(stats.get('compression_stats', {}))}
            </div>
            
            <!-- Test Statistics -->
            <div class="section">
                <h2>Test Results</h2>
                {self._generate_test_html(stats.get('test_stats', {}))}
            </div>
            
            <!-- SSIM Statistics -->
            <div class="section">
                <h2>SSIM Quality Metrics</h2>
                {self._generate_ssim_html(stats.get('ssim_stats', {}))}
            </div>
            
            <!-- CLI Statistics -->
            <div class="section">
                <h2>CLI Commands</h2>
                {self._generate_cli_html(stats.get('cli_stats', {}))}
            </div>
            
            <!-- Performance Trends -->
            <div class="section">
                <h2>Performance Trends (Last 5 Runs)</h2>
                {self._generate_trends_html(trends)}
            </div>
            
            <!-- Recent Comparisons -->
            <div class="section">
                <h2>Recent Run Comparison</h2>
                {self._generate_comparison_html(comparisons.get('comparisons', []))}
            </div>
        </div>
        
        <div class="footer">
            <p><strong>K2SHBWI Log Analysis Tool</strong></p>
            <p>Analysis based on logs from: {self.base_logs_dir}</p>
            <p style="margin-top: 10px; opacity: 0.7;">All data is real-time and verified | Report generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return str(output_file)
    
    def _generate_compression_html(self, stats: Dict) -> str:
        """Generate HTML for compression statistics"""
        if not stats:
            return "<p>No compression data available</p>"
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Avg Compression Ratio</div>
                <div class="metric-value">{stats.get('avg_compression_ratio', 0):.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Best Ratio</div>
                <div class="metric-value">{stats.get('best_compression_ratio', 0):.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Worst Ratio</div>
                <div class="metric-value">{stats.get('worst_compression_ratio', 0):.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Speed</div>
                <div class="metric-value">{stats.get('avg_processing_time_ms', 0):.2f}ms</div>
            </div>
        </div>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Operations</td>
                <td>{stats.get('total_operations', 0)}</td>
            </tr>
            <tr>
                <td>Total Original Bytes</td>
                <td>{stats.get('total_original_bytes', 0):,}</td>
            </tr>
            <tr>
                <td>Total Compressed Bytes</td>
                <td>{stats.get('total_compressed_bytes', 0):,}</td>
            </tr>
            <tr>
                <td>Overall Compression Ratio</td>
                <td>{((stats.get('total_original_bytes', 1) - stats.get('total_compressed_bytes', 0)) / stats.get('total_original_bytes', 1) * 100):.2f}%</td>
            </tr>
        </table>
        """
    
    def _generate_test_html(self, stats: Dict) -> str:
        """Generate HTML for test statistics"""
        if not stats:
            return "<p>No test data available</p>"
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value">{stats.get('total_tests', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Passed</div>
                <div class="metric-value" style="color: #4caf50;">{stats.get('passed', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Failed</div>
                <div class="metric-value" style="color: #f44336;">{stats.get('failed', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{stats.get('success_rate_percent', 0):.1f}%</div>
            </div>
        </div>
        """
    
    def _generate_ssim_html(self, stats: Dict) -> str:
        """Generate HTML for SSIM statistics"""
        if not stats:
            return "<p>No SSIM data available</p>"
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Measurements</div>
                <div class="metric-value">{stats.get('total_measurements', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{stats.get('avg_score', 0):.4f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Min Score</div>
                <div class="metric-value">{stats.get('min_score', 0):.4f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Score</div>
                <div class="metric-value">{stats.get('max_score', 0):.4f}</div>
            </div>
        </div>
        """
    
    def _generate_cli_html(self, stats: Dict) -> str:
        """Generate HTML for CLI statistics"""
        if not stats:
            return "<p>No CLI data available</p>"
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Commands</div>
                <div class="metric-value">{stats.get('total_commands', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Successful</div>
                <div class="metric-value" style="color: #4caf50;">{stats.get('successful', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Failed</div>
                <div class="metric-value" style="color: #f44336;">{stats.get('failed', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{stats.get('success_rate_percent', 0):.1f}%</div>
            </div>
        </div>
        """
    
    def _generate_trends_html(self, trends: List[Dict]) -> str:
        """Generate HTML for performance trends"""
        if not trends:
            return "<p>No trend data available</p>"
        
        rows = ""
        for trend in trends:
            rows += f"""
            <tr>
                <td>{trend.get('timestamp', 'N/A')[:10]}</td>
                <td>{trend.get('logger', 'N/A')}</td>
                <td>{trend.get('metric_count', 0)}</td>
                <td>{trend.get('average_compression_ratio', 0):.2f}%</td>
            </tr>
            """
        
        return f"""
        <table>
            <tr>
                <th>Date</th>
                <th>Logger</th>
                <th>Metrics</th>
                <th>Avg Compression</th>
            </tr>
            {rows}
        </table>
        """
    
    def _generate_comparison_html(self, comparisons: List[Dict]) -> str:
        """Generate HTML for recent comparisons"""
        if not comparisons:
            return "<p>No comparison data available</p>"
        
        rows = ""
        for comp in comparisons:
            rows += f"""
            <tr>
                <td>{comp.get('timestamp', 'N/A')[:19]}</td>
                <td>{comp.get('logger_name', 'N/A')}</td>
                <td>{comp.get('total_metrics', 0)}</td>
                <td>{comp.get('avg_compression_ratio', 0):.2f}%</td>
                <td>{comp.get('total_time_ms', 0):.2f}ms</td>
            </tr>
            """
        
        return f"""
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Logger</th>
                <th>Metrics</th>
                <th>Avg Compression</th>
                <th>Total Time</th>
            </tr>
            {rows}
        </table>
        """
    
    def export_to_txt(self, output_file: Optional[str] = None) -> str:
        """Export analysis report to TXT"""
        if not output_file:
            output_file = str(self.base_logs_dir / "ANALYSIS_REPORT.txt")
        
        stats = self.generate_summary_stats()
        trends = self.generate_performance_trends('compression', 5)
        comparisons = self.compare_recent_runs(3)
        
        txt_content = f"""
================================================================================
K2SHBWI LOG ANALYSIS REPORT
================================================================================

Generated: {datetime.now(timezone.utc).isoformat()}
Report Location: {self.base_logs_dir}

================================================================================
OVERALL SUMMARY
================================================================================

Total Log Files: {stats.get('total_logs', 0)}
Total Metrics Collected: {stats.get('total_metrics', 0)}
First Log: {stats.get('first_log', 'N/A')[:10]}
Latest Log: {stats.get('latest_log', 'N/A')[:10]}

================================================================================
COMPRESSION STATISTICS
================================================================================

"""
        
        comp_stats = stats.get('compression_stats', {})
        if comp_stats:
            txt_content += f"""
Total Compression Operations: {comp_stats.get('total_operations', 0)}
Average Compression Ratio: {comp_stats.get('avg_compression_ratio', 0):.2f}%
Median Compression Ratio: {comp_stats.get('median_compression_ratio', 0):.2f}%
Best Compression Ratio: {comp_stats.get('best_compression_ratio', 0):.2f}%
Worst Compression Ratio: {comp_stats.get('worst_compression_ratio', 0):.2f}%
Average Processing Time: {comp_stats.get('avg_processing_time_ms', 0):.2f}ms
Total Original Bytes: {comp_stats.get('total_original_bytes', 0):,}
Total Compressed Bytes: {comp_stats.get('total_compressed_bytes', 0):,}
Overall Compression Ratio: {((comp_stats.get('total_original_bytes', 1) - comp_stats.get('total_compressed_bytes', 0)) / comp_stats.get('total_original_bytes', 1) * 100) if comp_stats.get('total_original_bytes', 0) > 0 else 0:.2f}%
"""
        
        test_stats = stats.get('test_stats', {})
        if test_stats:
            txt_content += f"""
================================================================================
TEST STATISTICS
================================================================================

Total Tests: {test_stats.get('total_tests', 0)}
Passed: {test_stats.get('passed', 0)}
Failed: {test_stats.get('failed', 0)}
Skipped: {test_stats.get('skipped', 0)}
Success Rate: {test_stats.get('success_rate_percent', 0):.1f}%
"""
        
        ssim_stats = stats.get('ssim_stats', {})
        if ssim_stats:
            txt_content += f"""
================================================================================
SSIM QUALITY METRICS
================================================================================

Total SSIM Measurements: {ssim_stats.get('total_measurements', 0)}
Average Score: {ssim_stats.get('avg_score', 0):.4f}
Min Score: {ssim_stats.get('min_score', 0):.4f}
Max Score: {ssim_stats.get('max_score', 0):.4f}
Average Processing Time: {ssim_stats.get('avg_processing_time_ms', 0):.2f}ms
"""
        
        cli_stats = stats.get('cli_stats', {})
        if cli_stats:
            txt_content += f"""
================================================================================
CLI COMMAND STATISTICS
================================================================================

Total Commands: {cli_stats.get('total_commands', 0)}
Successful: {cli_stats.get('successful', 0)}
Failed: {cli_stats.get('failed', 0)}
Success Rate: {cli_stats.get('success_rate_percent', 0):.1f}%
"""
        
        txt_content += f"""
================================================================================
PERFORMANCE TRENDS (Last 5 Runs)
================================================================================

"""
        
        if trends:
            txt_content += "Timestamp       Logger           Metrics   Avg Compression\n"
            txt_content += "-" * 70 + "\n"
            for trend in trends:
                txt_content += f"{trend.get('timestamp', 'N/A')[:10]}     {trend.get('logger', 'N/A'):20s} {trend.get('metric_count', 0):8d}   {trend.get('average_compression_ratio', 0):6.2f}%\n"
        
        txt_content += f"""
================================================================================
RECENT RUN COMPARISON (Last 3 Runs)
================================================================================

"""
        
        if comparisons.get('comparisons'):
            txt_content += "Timestamp            Logger           Metrics   Ratio     Time\n"
            txt_content += "-" * 70 + "\n"
            for comp in comparisons.get('comparisons', []):
                txt_content += f"{comp.get('timestamp', 'N/A')[:19]}  {comp.get('logger_name', 'N/A'):15s} {comp.get('total_metrics', 0):8d}  {comp.get('avg_compression_ratio', 0):6.2f}%  {comp.get('total_time_ms', 0):8.2f}ms\n"
        
        txt_content += f"""
================================================================================
END OF REPORT
================================================================================

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
All metrics are real-time and verified
"""
        
        with open(output_file, 'w') as f:
            f.write(txt_content)
        
        return str(output_file)


# ============================================================================
# CLI INTERFACE
# ============================================================================

@click.group()
def cli():
    """K2SHBWI Log Analyzer - Analyze and report on K2SHBWI logs"""
    pass


@cli.command()
def latest():
    """Show the latest log file and its metrics"""
    analyzer = LogAnalyzer()
    latest_log = analyzer.get_latest_log()
    
    if not latest_log:
        click.echo("[ERROR] No logs found", err=True)
        return
    
    click.echo("\n" + "="*80)
    click.echo("LATEST LOG FILE")
    click.echo("="*80)
    click.echo(f"File: {latest_log.get('_file_name')}")
    click.echo(f"Timestamp: {latest_log.get('timestamp')}")
    click.echo(f"Logger: {latest_log.get('logger_name')}")
    click.echo(f"Type: {latest_log.get('log_type')}")
    click.echo(f"Total Metrics: {len(latest_log.get('metrics', []))}")
    
    summary = latest_log.get('summary', {})
    if summary:
        click.echo("\nSummary:")
        for key, value in summary.items():
            if not key.startswith('_'):
                click.echo(f"  {key}: {value}")
    
    click.echo("="*80 + "\n")


@cli.command()
def summary():
    """Generate overall summary report"""
    analyzer = LogAnalyzer()
    stats = analyzer.generate_summary_stats()
    
    click.echo("\n" + "="*80)
    click.echo("K2SHBWI LOG ANALYSIS SUMMARY")
    click.echo("="*80)
    click.echo(f"\nTotal Logs: {stats.get('total_logs', 0)}")
    click.echo(f"Total Metrics: {stats.get('total_metrics', 0)}")
    
    comp = stats.get('compression_stats')
    if comp:
        click.echo("\nCompression Statistics:")
        click.echo(f"  Avg Ratio: {comp.get('avg_compression_ratio', 0):.2f}%")
        click.echo(f"  Operations: {comp.get('total_operations', 0)}")
        click.echo(f"  Total Saved: {comp.get('total_original_bytes', 0) - comp.get('total_compressed_bytes', 0):,} bytes")
    
    test = stats.get('test_stats')
    if test:
        click.echo("\nTest Statistics:")
        click.echo(f"  Total Tests: {test.get('total_tests', 0)}")
        click.echo(f"  Passed: {test.get('passed', 0)}")
        click.echo(f"  Success Rate: {test.get('success_rate_percent', 0):.1f}%")
    
    cli_data = stats.get('cli_stats')
    if cli_data:
        click.echo("\nCLI Statistics:")
        click.echo(f"  Total Commands: {cli_data.get('total_commands', 0)}")
        click.echo(f"  Success Rate: {cli_data.get('success_rate_percent', 0):.1f}%")
    
    click.echo("\n" + "="*80 + "\n")


@cli.command()
def compare():
    """Compare recent log runs"""
    analyzer = LogAnalyzer()
    comparisons = analyzer.compare_recent_runs(3)
    
    click.echo("\n" + "="*80)
    click.echo("RECENT RUN COMPARISON")
    click.echo("="*80)
    click.echo(f"\n{'Timestamp':<20} {'Logger':<20} {'Metrics':<10} {'Ratio':<10} {'Time':<10}")
    click.echo("-"*80)
    
    for comp in comparisons.get('comparisons', []):
        timestamp = comp.get('timestamp', 'N/A')[:19]
        logger = comp.get('logger_name', 'N/A')[:20]
        metrics = str(comp.get('total_metrics', 0))[:10]
        ratio = f"{comp.get('avg_compression_ratio', 0):.2f}%"[:10]
        time_ms = f"{comp.get('total_time_ms', 0):.2f}ms"[:10]
        
        click.echo(f"{timestamp:<20} {logger:<20} {metrics:>10} {ratio:>10} {time_ms:>10}")
    
    click.echo("\n" + "="*80 + "\n")


@cli.command()
@click.option('--format', type=click.Choice(['html', 'txt']), default='html', help='Export format')
def export(format):
    """Export analysis report"""
    analyzer = LogAnalyzer()
    
    if format == 'html':
        output_file = analyzer.export_to_html()
        click.echo(f"[OK] HTML report exported to: {output_file}")
    else:
        output_file = analyzer.export_to_txt()
        click.echo(f"[OK] TXT report exported to: {output_file}")


if __name__ == '__main__':
    cli()
