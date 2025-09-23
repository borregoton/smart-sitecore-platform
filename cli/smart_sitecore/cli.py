#!/usr/bin/env python3
"""
Smart Sitecore CLI - Main Entry Point
Project20 v2.0 - Direct API, No Mock Data

Usage:
    smart-sitecore analyze <url> [--categories content,templates]
    smart-sitecore report <scan-id> [--format html]
    smart-sitecore history [--limit 10]
    smart-sitecore config set <key> <value>
"""

import click
import json
import asyncio
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from .config import Config, SitecoreCredentials
from .analyzers.content import ContentAnalyzer
from .analyzers.templates import TemplateAnalyzer
from .analyzers.performance import PerformanceAnalyzer
from .analyzers.seo import SEOAnalyzer
from .analyzers.security import SecurityAnalyzer

console = Console()

# Available analyzers
ANALYZERS = {
    'content': ContentAnalyzer,
    'templates': TemplateAnalyzer,
    'performance': PerformanceAnalyzer,
    'seo': SEOAnalyzer,
    'security': SecurityAnalyzer
}

CATEGORY_DESCRIPTIONS = {
    'content': 'Content Management - Items, depth, organization',
    'templates': 'Template Analysis - Structure, fields, inheritance',
    'performance': 'Performance Metrics - Core Web Vitals, speed',
    'seo': 'SEO Analysis - Meta tags, structured data',
    'security': 'Security Assessment - Headers, HTTPS, CSP'
}


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Smart Sitecore Health Assessment CLI - Real Data Only"""
    pass


@cli.command()
@click.argument('url')
@click.option('--categories',
              default='content,templates,performance,seo,security',
              help='Comma-separated list of categories to analyze')
@click.option('--api-key',
              help='Sitecore API key for GraphQL access')
@click.option('--username',
              help='Sitecore username for basic auth')
@click.option('--password',
              help='Sitecore password for basic auth')
@click.option('--save/--no-save',
              default=True,
              help='Save results to database')
@click.option('--format',
              type=click.Choice(['json', 'table', 'detailed']),
              default='detailed',
              help='Output format')
def analyze(url: str, categories: str, api_key: Optional[str],
           username: Optional[str], password: Optional[str],
           save: bool, format: str):
    """Analyze a Sitecore site for health metrics"""

    console.print("\n[bold blue]>> Smart Sitecore Health Assessment[/bold blue]")
    console.print(f"[dim]Project20 v2.0 - Real Data Only[/dim]\n")

    # Parse categories
    category_list = [cat.strip().lower() for cat in categories.split(',')]
    invalid_categories = [cat for cat in category_list if cat not in ANALYZERS]

    if invalid_categories:
        console.print(f"[red]ERROR: Invalid categories: {', '.join(invalid_categories)}[/red]")
        console.print(f"[yellow]Available: {', '.join(ANALYZERS.keys())}[/yellow]")
        sys.exit(1)

    # Load configuration
    config = Config()

    # Set up credentials if provided
    credentials = None
    if api_key:
        credentials = SitecoreCredentials(
            url=url,
            api_key=api_key,
            auth_type='apikey'
        )
    elif username and password:
        credentials = SitecoreCredentials(
            url=url,
            username=username,
            password=password,
            auth_type='basic'
        )
    else:
        # Try to load from config
        credentials = config.get_credentials(url)

    if not credentials:
        console.print(f"[red]ERROR: No credentials found for {url}[/red]")
        console.print(f"[yellow]TIP: Provide credentials with --api-key or --username/--password[/yellow]")
        console.print(f"[yellow]TIP: Or save them with: smart-sitecore config set-credentials[/yellow]")
        sys.exit(1)

    # Run analysis
    results = asyncio.run(run_analysis(url, category_list, credentials))

    # Display results
    if format == 'json':
        console.print(json.dumps(results, indent=2))
    elif format == 'table':
        display_table_results(results)
    else:
        display_detailed_results(results)

    # Save results if requested
    if save:
        scan_id = save_results(results, config)
        console.print(f"\n[green]SUCCESS: Results saved with ID: {scan_id}[/green]")


async def run_analysis(url: str, categories: List[str], credentials: SitecoreCredentials) -> Dict[str, Any]:
    """Run analysis for specified categories"""

    results = {
        'scan_id': f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'categories': {},
        'overall_score': 0,
        'status': 'completed'
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        total_score = 0
        completed_categories = 0

        for category in categories:
            task = progress.add_task(f"Analyzing {category}...", total=None)

            try:
                analyzer_class = ANALYZERS[category]
                analyzer = analyzer_class(credentials)

                category_result = await analyzer.analyze(url)
                results['categories'][category] = category_result

                if category_result['status'] == 'success':
                    total_score += category_result['score']
                    completed_categories += 1
                    progress.update(task, description=f"OK {category.title()} - Score: {category_result['score']}")
                else:
                    progress.update(task, description=f"FAIL {category.title()} - {category_result.get('error', 'Failed')}")

            except Exception as e:
                results['categories'][category] = {
                    'status': 'error',
                    'error': str(e),
                    'score': 0
                }
                progress.update(task, description=f"ERROR {category.title()} - Error: {str(e)}")

            await asyncio.sleep(0.1)  # Small delay for progress display

    # Calculate overall score
    if completed_categories > 0:
        results['overall_score'] = round(total_score / completed_categories)

    return results


def display_detailed_results(results: Dict[str, Any]):
    """Display detailed analysis results"""

    console.print(f"\n[bold]>> Analysis Results for {results['url']}[/bold]")
    console.print(f"[dim]Scan ID: {results['scan_id']} | {results['timestamp']}[/dim]\n")

    # Overall score
    score = results['overall_score']
    if score >= 80:
        score_color = "green"
        score_status = "EXCELLENT"
    elif score >= 60:
        score_color = "yellow"
        score_status = "GOOD"
    else:
        score_color = "red"
        score_status = "NEEDS WORK"

    console.print(Panel(
        f"[bold {score_color}]{score_status} - Overall Score: {score}/100[/bold {score_color}]",
        title="Health Score",
        border_style=score_color
    ))

    # Category details
    for category, data in results['categories'].items():
        if data['status'] == 'success':
            display_category_success(category, data)
        else:
            display_category_error(category, data)


def display_category_success(category: str, data: Dict[str, Any]):
    """Display successful category analysis"""

    score = data['score']
    if score >= 80:
        color = "green"
        status = "PASS"
    elif score >= 60:
        color = "yellow"
        status = "WARN"
    else:
        color = "red"
        status = "FAIL"

    tree = Tree(f"[bold]{status} {category.title()} - Score: {score}/100[/bold]")

    # Add metrics
    if 'metrics' in data:
        metrics_branch = tree.add("[cyan]METRICS[/cyan]")
        for key, value in data['metrics'].items():
            metrics_branch.add(f"{key}: {value}")

    # Add issues
    if 'issues' in data and data['issues']:
        issues_branch = tree.add(f"[yellow]ISSUES ({len(data['issues'])})[/yellow]")
        for issue in data['issues'][:5]:  # Show top 5
            issues_branch.add(f"- {issue}")

    # Add recommendations
    if 'recommendations' in data and data['recommendations']:
        rec_branch = tree.add(f"[green]RECOMMENDATIONS ({len(data['recommendations'])})[/green]")
        for rec in data['recommendations'][:3]:  # Show top 3
            rec_branch.add(f"- {rec}")

    console.print(tree)
    console.print()


def display_category_error(category: str, data: Dict[str, Any]):
    """Display failed category analysis"""

    error_msg = data.get('error', 'Unknown error')

    console.print(Panel(
        f"[red]FAILED - {category.title()} Analysis Failed[/red]\n"
        f"[dim]Error: {error_msg}[/dim]\n\n"
        f"[yellow]TROUBLESHOOTING:[/yellow]\n"
        f"- Check network connectivity to the Sitecore instance\n"
        f"- Verify API credentials are correct\n"
        f"- Ensure GraphQL endpoint is enabled\n"
        f"- Check if the site is accessible",
        title=f"{category.title()} Error",
        border_style="red"
    ))


def display_table_results(results: Dict[str, Any]):
    """Display results in table format"""

    table = Table(title=f"Analysis Results - {results['url']}")
    table.add_column("Category", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="center")
    table.add_column("Key Metrics", style="dim")

    for category, data in results['categories'].items():
        status = "PASS" if data['status'] == 'success' else "FAIL"
        score = str(data.get('score', 0))

        # Summarize key metrics
        key_metrics = ""
        if data['status'] == 'success' and 'metrics' in data:
            metrics = data['metrics']
            key_items = list(metrics.items())[:2]  # Show first 2 metrics
            key_metrics = ", ".join([f"{k}: {v}" for k, v in key_items])

        table.add_row(category.title(), status, score, key_metrics)

    console.print(table)


def save_results(results: Dict[str, Any], config: Config) -> str:
    """Save results to database/file"""

    # For POC, save to local file (in production, save to Supabase)
    scan_id = results['scan_id']
    filename = f"{config.get_data_dir()}/{scan_id}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        return scan_id
    except Exception as e:
        console.print(f"[red]ERROR: Failed to save results: {e}[/red]")
        return scan_id


@cli.command()
@click.argument('scan_id')
@click.option('--format',
              type=click.Choice(['html', 'json', 'pdf']),
              default='html',
              help='Report format')
def report(scan_id: str, format: str):
    """Generate a report from saved scan results"""
    console.print(f"[blue]REPORT: Generating {format.upper()} report for {scan_id}[/blue]")
    # TODO: Implement report generation
    console.print("[yellow]WARNING: Report generation coming in next iteration[/yellow]")


@cli.command()
@click.option('--limit', default=10, help='Number of recent scans to show')
def history(limit: int):
    """Show scan history"""
    console.print(f"[blue]HISTORY: Recent {limit} scans[/blue]")
    # TODO: Implement history from database
    console.print("[yellow]WARNING: History feature coming in next iteration[/yellow]")


@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('set-credentials')
@click.argument('url')
@click.option('--api-key', help='Sitecore API key')
@click.option('--username', help='Username for basic auth')
@click.option('--password', help='Password for basic auth')
def set_credentials(url: str, api_key: Optional[str], username: Optional[str], password: Optional[str]):
    """Save Sitecore credentials for a site"""

    config_obj = Config()

    if api_key:
        credentials = SitecoreCredentials(
            url=url,
            api_key=api_key,
            auth_type='apikey'
        )
    elif username and password:
        credentials = SitecoreCredentials(
            url=url,
            username=username,
            password=password,
            auth_type='basic'
        )
    else:
        console.print("[red]ERROR: Provide either --api-key or --username/--password[/red]")
        sys.exit(1)

    config_obj.save_credentials(url, credentials)
    console.print(f"[green]SUCCESS: Credentials saved for {url}[/green]")


if __name__ == '__main__':
    cli()