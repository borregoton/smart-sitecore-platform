#!/usr/bin/env python3
"""
Enhanced HTML Report Generator with Comparison
Tests both original and enhanced content analyzers
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, 'cli')

from smart_sitecore.config import SitecoreCredentials
from smart_sitecore.analyzers.content import ContentAnalyzer
from smart_sitecore.analyzers.content_enhanced import EnhancedContentAnalyzer


class ComparisonReporter:
    """Compare original vs enhanced content analysis"""

    def __init__(self, url: str, credentials: SitecoreCredentials):
        self.url = url
        self.credentials = credentials
        self.original_results = {}
        self.enhanced_results = {}
        self.comparison_data = {}

    async def run_comparison_analysis(self):
        """Run both analyzers and compare results"""

        print(f"🔍 Running comparison analysis of {self.url}...")
        print("=" * 60)

        # Test original analyzer
        print("\n📊 ORIGINAL ANALYZER")
        print("-" * 20)
        start_time = time.time()

        try:
            original_analyzer = ContentAnalyzer(self.credentials)
            original_result = await original_analyzer.analyze(self.url)

            self.original_results = {
                'status': original_result.status,
                'score': original_result.score,
                'metrics': original_result.metrics,
                'issues': original_result.issues,
                'recommendations': original_result.recommendations,
                'api_calls': original_result.api_calls_made,
                'execution_time': original_result.execution_time,
                'data_source': original_result.data_source
            }

            print(f"✅ Status: {original_result.status}")
            print(f"📈 Score: {original_result.score}/100")
            print(f"🌐 API Calls: {original_result.api_calls_made}")
            print(f"⏱️  Time: {original_result.execution_time:.2f}s")

        except Exception as e:
            print(f"❌ Original analyzer failed: {e}")
            self.original_results = {'status': 'error', 'error': str(e)}

        # Test enhanced analyzer
        print("\n🚀 ENHANCED ANALYZER")
        print("-" * 20)

        try:
            enhanced_analyzer = EnhancedContentAnalyzer(self.credentials)
            enhanced_result = await enhanced_analyzer.analyze(self.url)

            self.enhanced_results = {
                'status': enhanced_result.status,
                'score': enhanced_result.score,
                'metrics': enhanced_result.metrics,
                'issues': enhanced_result.issues,
                'recommendations': enhanced_result.recommendations,
                'api_calls': enhanced_result.api_calls_made,
                'execution_time': enhanced_result.execution_time,
                'data_source': enhanced_result.data_source
            }

            print(f"✅ Status: {enhanced_result.status}")
            print(f"📈 Score: {enhanced_result.score}/100")
            print(f"🌐 API Calls: {enhanced_result.api_calls_made}")
            print(f"⏱️  Time: {enhanced_result.execution_time:.2f}s")

            # Show enhanced metrics
            metrics = enhanced_result.metrics
            print(f"🎯 Analysis Depth: {metrics.get('analysis_depth', 'unknown')}")
            print(f"📋 Templates Found: {len(metrics.get('templates_used', {}))}")
            print(f"🔧 Field Completeness Data: {len(metrics.get('field_completeness', {}))}")

        except Exception as e:
            print(f"❌ Enhanced analyzer failed: {e}")
            self.enhanced_results = {'status': 'error', 'error': str(e)}

        # Generate comparison
        self._generate_comparison()

        return {
            'original': self.original_results,
            'enhanced': self.enhanced_results,
            'comparison': self.comparison_data
        }

    def _generate_comparison(self):
        """Generate comparison analysis"""
        if (self.original_results.get('status') == 'success' and
            self.enhanced_results.get('status') == 'success'):

            print("\n📊 COMPARISON ANALYSIS")
            print("-" * 30)

            # Score improvement
            original_score = self.original_results['score']
            enhanced_score = self.enhanced_results['score']
            score_change = enhanced_score - original_score

            print(f"📈 Score Change: {original_score} → {enhanced_score} ({score_change:+d} points)")

            # API efficiency
            orig_api = self.original_results['api_calls']
            enh_api = self.enhanced_results['api_calls']
            orig_items = self.original_results['metrics'].get('total_content_items', 1)
            enh_items = self.enhanced_results['metrics'].get('total_items', 1)

            orig_efficiency = orig_api / max(orig_items, 1)
            enh_efficiency = enh_api / max(enh_items, 1)

            print(f"🌐 API Efficiency: {orig_efficiency:.2f} → {enh_efficiency:.2f} calls/item")

            # Data richness
            orig_metrics = len(self.original_results['metrics'])
            enh_metrics = len(self.enhanced_results['metrics'])

            print(f"📊 Metrics Richness: {orig_metrics} → {enh_metrics} data points")

            # Analysis depth
            enh_depth = self.enhanced_results['metrics'].get('analysis_depth', 'basic')
            print(f"🎯 Analysis Depth: basic → {enh_depth}")

            self.comparison_data = {
                'score_improvement': score_change,
                'api_efficiency_change': enh_efficiency - orig_efficiency,
                'metrics_richness_improvement': enh_metrics - orig_metrics,
                'analysis_depth_achieved': enh_depth
            }

    def generate_enhanced_html_report(self) -> str:
        """Generate enhanced HTML report with comparison"""

        # Determine which results to use for main report
        if self.enhanced_results.get('status') == 'success':
            primary_results = self.enhanced_results
            analyzer_type = "Enhanced"
        else:
            primary_results = self.original_results
            analyzer_type = "Original"

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Sitecore Health Report - {self.url}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f5f7fa; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
        .score-badge {{ font-size: 56px; font-weight: bold; margin: 15px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .score-excellent {{ color: #10b981; }}
        .score-good {{ color: #f59e0b; }}
        .score-poor {{ color: #ef4444; }}

        .comparison-section {{ background: white; padding: 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .comparison-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .comparison-item {{ text-align: center; padding: 20px; background: #f8fafc; border-radius: 8px; }}
        .comparison-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .improvement {{ color: #10b981; }}
        .decline {{ color: #ef4444; }}

        .category {{ margin: 25px 0; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .category-success {{ background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left: 6px solid #10b981; }}
        .category-error {{ background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-left: 6px solid #ef4444; }}

        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .metric-label {{ font-weight: 600; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 20px; color: #1f2937; margin-top: 8px; }}

        .enhanced-metrics {{ background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .enhanced-title {{ color: #0284c7; font-weight: bold; margin-bottom: 15px; }}

        .issues {{ margin: 20px 0; }}
        .issue {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 8px 0; border-radius: 6px; }}
        .recommendation {{ background: #ecfdf5; border-left: 4px solid #10b981; padding: 12px 16px; margin: 8px 0; border-radius: 6px; }}

        .timestamp {{ text-align: center; color: #6b7280; margin-top: 40px; padding: 20px; }}
        .analyzer-badge {{ display: inline-block; background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="analyzer-badge">{analyzer_type} Analyzer</div>
            <h1>Enhanced Sitecore Health Assessment</h1>
            <p><strong>Site:</strong> {self.url}</p>
            <div class="score-badge {self._get_score_class(primary_results.get('score', 0))}">
                {primary_results.get('score', 0)}/100
            </div>
        </div>

        {self._generate_comparison_html()}
        {self._generate_enhanced_analysis_html()}

        <div class="timestamp">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Analyzer:</strong> {analyzer_type} Content Analysis Engine</p>
            <p><strong>API Calls:</strong> {primary_results.get('api_calls', 0)} | <strong>Execution Time:</strong> {primary_results.get('execution_time', 0):.2f}s</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return html

    def _generate_comparison_html(self) -> str:
        """Generate comparison section HTML"""
        if not self.comparison_data:
            return ""

        html = f"""
        <div class="comparison-section">
            <h2>📊 Enhancement Analysis</h2>
            <div class="comparison-grid">
                <div class="comparison-item">
                    <div class="metric-label">Score Improvement</div>
                    <div class="comparison-value {self._get_change_class(self.comparison_data.get('score_improvement', 0))}">
                        {self.comparison_data.get('score_improvement', 0):+d} points
                    </div>
                </div>
                <div class="comparison-item">
                    <div class="metric-label">API Efficiency</div>
                    <div class="comparison-value {self._get_change_class(-self.comparison_data.get('api_efficiency_change', 0))}">
                        {self.comparison_data.get('api_efficiency_change', 0):+.2f} calls/item
                    </div>
                </div>
                <div class="comparison-item">
                    <div class="metric-label">Data Richness</div>
                    <div class="comparison-value {self._get_change_class(self.comparison_data.get('metrics_richness_improvement', 0))}">
                        {self.comparison_data.get('metrics_richness_improvement', 0):+d} metrics
                    </div>
                </div>
                <div class="comparison-item">
                    <div class="metric-label">Analysis Depth</div>
                    <div class="comparison-value improvement">
                        {self.comparison_data.get('analysis_depth_achieved', 'enhanced')}
                    </div>
                </div>
            </div>
        </div>
        """
        return html

    def _generate_enhanced_analysis_html(self) -> str:
        """Generate enhanced analysis results HTML"""
        if self.enhanced_results.get('status') != 'success':
            return '<div class="category category-error"><h2>Enhanced Analysis Failed</h2><p>Using original analysis results.</p></div>'

        metrics = self.enhanced_results['metrics']
        issues = self.enhanced_results.get('issues', [])
        recommendations = self.enhanced_results.get('recommendations', [])

        html = f'<div class="category category-success">'
        html += f'<h2>🚀 Enhanced Content Analysis</h2>'
        html += f'<p><strong>Score:</strong> <span class="{self._get_score_class(self.enhanced_results["score"])}">{self.enhanced_results["score"]}/100</span></p>'
        html += f'<p><strong>Analysis Depth:</strong> {metrics.get("analysis_depth", "unknown").title()}</p>'

        # Basic Metrics
        html += '<h3>📊 Core Metrics</h3>'
        html += '<div class="metrics-grid">'

        basic_metrics = {
            'Total Items': metrics.get('total_items', 0),
            'Total Sites': metrics.get('total_sites', 0),
            'Max Depth': metrics.get('max_depth', 0),
            'API Efficiency': f"{self.enhanced_results.get('api_calls', 0) / max(metrics.get('total_items', 1), 1):.2f} calls/item"
        }

        for label, value in basic_metrics.items():
            html += f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>'

        html += '</div>'

        # Enhanced Metrics
        if metrics.get('templates_used'):
            html += '<div class="enhanced-metrics">'
            html += '<div class="enhanced-title">🎨 Template Analysis</div>'
            html += '<div class="metrics-grid">'

            for template, count in list(metrics['templates_used'].items())[:6]:
                html += f'<div class="metric"><div class="metric-label">{template}</div><div class="metric-value">{count} items</div></div>'

            html += '</div></div>'

        # Field Completeness
        if metrics.get('field_completeness'):
            html += '<div class="enhanced-metrics">'
            html += '<div class="enhanced-title">📋 Field Completeness Analysis</div>'
            html += '<div class="metrics-grid">'

            for template, data in list(metrics['field_completeness'].items())[:4]:
                overall_score = data.get('overall', 0)
                html += f'<div class="metric"><div class="metric-label">{template}</div><div class="metric-value {self._get_score_class(overall_score)}">{overall_score}% complete</div></div>'

            html += '</div></div>'

        # Content Quality
        if metrics.get('content_quality_scores'):
            html += '<div class="enhanced-metrics">'
            html += '<div class="enhanced-title">⭐ Content Quality Scores</div>'
            html += '<div class="metrics-grid">'

            for template, score in list(metrics['content_quality_scores'].items())[:4]:
                html += f'<div class="metric"><div class="metric-label">{template}</div><div class="metric-value {self._get_score_class(score)}">{score}/100</div></div>'

            html += '</div></div>'

        # Issues
        if issues:
            html += '<h3>⚠️  Issues Identified</h3>'
            html += '<div class="issues">'
            for issue in issues:
                html += f'<div class="issue">{issue}</div>'
            html += '</div>'

        # Recommendations
        if recommendations:
            html += '<h3>💡 Recommendations</h3>'
            html += '<div class="issues">'
            for rec in recommendations:
                html += f'<div class="recommendation">{rec}</div>'
            html += '</div>'

        html += '</div>'
        return html

    def _get_score_class(self, score: int) -> str:
        """Get CSS class for score"""
        if score >= 80:
            return 'score-excellent'
        elif score >= 60:
            return 'score-good'
        else:
            return 'score-poor'

    def _get_change_class(self, change: float) -> str:
        """Get CSS class for change value"""
        if change > 0:
            return 'improvement'
        elif change < 0:
            return 'decline'
        else:
            return ''


async def main():
    """Run the enhanced reporter test"""

    url = "https://cm-qa-sc103.kajoo.ca"
    credentials = SitecoreCredentials(
        url=url,
        auth_type='apikey',
        api_key='{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}'
    )

    print("🚀 Enhanced Sitecore Analysis Comparison")
    print("=" * 50)

    reporter = ComparisonReporter(url, credentials)

    # Run comparison analysis
    results = await reporter.run_comparison_analysis()

    # Generate enhanced HTML report
    print("\n📄 Generating enhanced HTML report...")
    html_content = reporter.generate_enhanced_html_report()

    # Save the report
    report_file = f"enhanced_sitecore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Enhanced report saved: {report_file}")
    print(f"📊 Report size: {len(html_content):,} characters")

    # Summary
    print("\n🎯 ANALYSIS SUMMARY")
    print("-" * 30)
    if results['enhanced']['status'] == 'success':
        print("✅ Enhanced analyzer working successfully")
        print(f"📈 Score: {results['enhanced']['score']}/100")
        print(f"🎯 Analysis depth: {results['enhanced']['metrics'].get('analysis_depth', 'unknown')}")
        print(f"📊 Templates analyzed: {len(results['enhanced']['metrics'].get('templates_used', {}))}")
        print(f"🔧 Field completeness data: {len(results['enhanced']['metrics'].get('field_completeness', {}))}")
    else:
        print("❌ Enhanced analyzer had issues")

    return results


if __name__ == "__main__":
    asyncio.run(main())