#!/usr/bin/env python3
"""
Simple HTML Report Generator for Sitecore CLI
Bypasses Rich progress interface to avoid Unicode issues on Windows
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Minimal imports to avoid dependencies
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cli'))

from smart_sitecore.config import SitecoreCredentials
from smart_sitecore.analyzers.content import ContentAnalyzer
from smart_sitecore.analyzers.templates import TemplateAnalyzer


class SimpleHtmlReporter:
    """Generate HTML reports without Rich dependencies"""

    def __init__(self, url: str, credentials: SitecoreCredentials):
        self.url = url
        self.credentials = credentials
        self.results = {}

    async def run_analysis(self, categories: List[str] = None):
        """Run analysis without Rich progress bars"""

        if not categories:
            categories = ['content', 'templates']

        analyzers = {
            'content': ContentAnalyzer,
            'templates': TemplateAnalyzer
        }

        self.results = {
            'url': self.url,
            'timestamp': datetime.now().isoformat(),
            'categories': {},
            'overall_score': 0,
            'errors': []
        }

        print(f"Starting analysis of {self.url}...")

        total_score = 0
        successful_categories = 0

        for category in categories:
            if category not in analyzers:
                print(f"  SKIP: Unknown category '{category}'")
                continue

            print(f"  Running {category} analysis...")

            try:
                analyzer_class = analyzers[category]
                analyzer = analyzer_class(self.credentials)

                # Run the analysis
                result = await analyzer.analyze(self.url)

                self.results['categories'][category] = {
                    'status': result.status,
                    'score': result.score,
                    'metrics': result.metrics,
                    'issues': result.issues,
                    'recommendations': result.recommendations,
                    'data_source': result.data_source
                }

                if result.status == 'success':
                    total_score += result.score
                    successful_categories += 1
                    print(f"    SUCCESS: {category} - Score: {result.score}/100")
                else:
                    error_msg = result.error or "Unknown error"
                    print(f"    FAILED: {category} - {error_msg}")

            except Exception as e:
                error_msg = str(e)
                print(f"    ERROR: {category} - {error_msg}")

                self.results['categories'][category] = {
                    'status': 'error',
                    'score': 0,
                    'error': error_msg
                }
                self.results['errors'].append(f"{category}: {error_msg}")

        # Calculate overall score
        if successful_categories > 0:
            self.results['overall_score'] = round(total_score / successful_categories)

        print(f"Analysis complete. Overall score: {self.results['overall_score']}/100")
        return self.results

    def generate_html_report(self) -> str:
        """Generate HTML report from results"""

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitecore Health Report - {self.url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: #003f7f; color: white; border-radius: 8px; }}
        .score-badge {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .score-excellent {{ color: #28a745; }}
        .score-good {{ color: #ffc107; }}
        .score-poor {{ color: #dc3545; }}
        .category {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .category-success {{ border-left: 5px solid #28a745; background: #f8fff9; }}
        .category-error {{ border-left: 5px solid #dc3545; background: #fff8f8; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
        .metric {{ padding: 10px; background: #f8f9fa; border-radius: 4px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 18px; color: #333; }}
        .issues, .recommendations {{ margin: 15px 0; }}
        .issue {{ color: #dc3545; margin: 5px 0; }}
        .recommendation {{ color: #17a2b8; margin: 5px 0; }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; }}
        .error-summary {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sitecore Health Assessment Report</h1>
            <p><strong>Site:</strong> {self.url}</p>
            <div class="score-badge {self._get_score_class(self.results.get('overall_score', 0))}">
                {self.results.get('overall_score', 0)}/100
            </div>
        </div>

        {self._generate_error_summary()}
        {self._generate_categories_html()}

        <div class="timestamp">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Analysis timestamp: {self.results.get('timestamp', 'Unknown')}</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return html

    def _get_score_class(self, score: int) -> str:
        """Get CSS class for score"""
        if score >= 80:
            return 'score-excellent'
        elif score >= 60:
            return 'score-good'
        else:
            return 'score-poor'

    def _generate_error_summary(self) -> str:
        """Generate error summary HTML"""
        errors = self.results.get('errors', [])
        if not errors:
            return ""

        html = '<div class="error-summary">'
        html += '<h3>Analysis Errors</h3>'
        html += '<ul>'
        for error in errors:
            html += f'<li>{error}</li>'
        html += '</ul>'
        html += '</div>'
        return html

    def _generate_categories_html(self) -> str:
        """Generate categories section HTML"""
        categories = self.results.get('categories', {})
        if not categories:
            return '<p>No analysis categories available.</p>'

        html = ""
        for category_name, category_data in categories.items():
            status = category_data.get('status', 'unknown')
            score = category_data.get('score', 0)

            category_class = 'category-success' if status == 'success' else 'category-error'

            html += f'<div class="category {category_class}">'
            html += f'<h2>{category_name.title()} Analysis</h2>'

            if status == 'success':
                html += f'<p><strong>Score:</strong> <span class="{self._get_score_class(score)}">{score}/100</span></p>'

                # Metrics
                metrics = category_data.get('metrics', {})
                if metrics:
                    html += '<h3>Metrics</h3>'
                    html += '<div class="metrics">'
                    for key, value in metrics.items():
                        html += f'<div class="metric">'
                        html += f'<div class="metric-label">{key.replace("_", " ").title()}</div>'
                        html += f'<div class="metric-value">{value}</div>'
                        html += '</div>'
                    html += '</div>'

                # Issues
                issues = category_data.get('issues', [])
                if issues:
                    html += '<h3>Issues</h3>'
                    html += '<div class="issues">'
                    for issue in issues:
                        html += f'<div class="issue">• {issue}</div>'
                    html += '</div>'

                # Recommendations
                recommendations = category_data.get('recommendations', [])
                if recommendations:
                    html += '<h3>Recommendations</h3>'
                    html += '<div class="recommendations">'
                    for rec in recommendations:
                        html += f'<div class="recommendation">• {rec}</div>'
                    html += '</div>'

            else:
                # Error case
                error = category_data.get('error', 'Unknown error')
                html += f'<p><strong>Status:</strong> <span style="color: #dc3545;">Failed</span></p>'
                html += f'<p><strong>Error:</strong> {error}</p>'

            html += '</div>'

        return html


async def main():
    """Test the HTML reporter"""

    # Test with the known Sitecore endpoint
    url = "https://cm-qa-sc103.kajoo.ca"

    # Use the real API key found in the project
    credentials = SitecoreCredentials(
        url=url,
        auth_type='apikey',
        api_key='{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}'
    )

    print("Creating HTML reporter...")
    reporter = SimpleHtmlReporter(url, credentials)

    print("Running analysis...")
    await reporter.run_analysis(['content', 'templates'])

    print("Generating HTML report...")
    html_content = reporter.generate_html_report()

    # Save the report
    report_file = f"sitecore_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML report saved to: {report_file}")
    print(f"Report size: {len(html_content)} characters")

    # Show summary
    print("\nReport Summary:")
    print(f"  Overall Score: {reporter.results.get('overall_score', 0)}/100")
    print(f"  Categories: {len(reporter.results.get('categories', {}))}")
    print(f"  Errors: {len(reporter.results.get('errors', []))}")


if __name__ == "__main__":
    asyncio.run(main())