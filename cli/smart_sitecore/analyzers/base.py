"""
Base Analyzer Class
Project20 v2.0 - Real Data Only

This is the foundation class for all category analyzers.
It enforces the NO MOCK DATA principle throughout the system.

Key Principles:
1. Real data or clear error - never simulate success
2. Fail fast with descriptive error messages
3. Provide actionable troubleshooting guidance
4. Log all API calls and responses for debugging
"""

import asyncio
import aiohttp
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..config import SitecoreCredentials


class AnalysisError(Exception):
    """Custom exception for analysis failures"""

    def __init__(self, message: str, category: str, url: str,
                 troubleshooting: Optional[List[str]] = None):
        self.message = message
        self.category = category
        self.url = url
        self.troubleshooting = troubleshooting or []
        super().__init__(self.message)


@dataclass
class AnalysisResult:
    """Standard result structure for all analyzers"""
    category: str
    status: str  # 'success', 'error', 'partial'
    score: int  # 0-100
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    api_calls_made: int = 0
    data_source: str = "unknown"  # Track where data came from
    error: Optional[str] = None
    troubleshooting: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'category': self.category,
            'status': self.status,
            'score': self.score,
            'metrics': self.metrics,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'execution_time': self.execution_time,
            'api_calls_made': self.api_calls_made,
            'data_source': self.data_source,
            'error': self.error,
            'troubleshooting': self.troubleshooting,
            'timestamp': datetime.now().isoformat()
        }


class BaseAnalyzer(ABC):
    """
    Base class for all category analyzers

    CRITICAL: This class enforces the NO MOCK DATA principle.
    All subclasses MUST return real data or clear errors.
    """

    def __init__(self, credentials: SitecoreCredentials):
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
        self.start_time = 0.0
        self.api_calls_made = 0

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Return the category name (e.g., 'content', 'templates')"""
        pass

    @property
    @abstractmethod
    def requires_sitecore_access(self) -> bool:
        """Return True if this analyzer needs Sitecore backend access"""
        pass

    @property
    def timeout(self) -> int:
        """Request timeout in seconds"""
        return 30

    @property
    def max_retries(self) -> int:
        """Maximum retry attempts for failed requests"""
        return 2

    async def analyze(self, url: str) -> AnalysisResult:
        """
        Main analysis entry point

        Args:
            url: URL to analyze

        Returns:
            AnalysisResult with real data or clear error
        """
        self.start_time = time.time()
        result = AnalysisResult(category=self.category_name, status='error', score=0)

        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.credentials.get_headers()
            )

            # Pre-flight checks
            await self._validate_prerequisites(url)

            # Run the actual analysis
            result = await self._run_analysis(url)

        except AnalysisError as e:
            result.status = 'error'
            result.error = e.message
            result.troubleshooting = e.troubleshooting

        except Exception as e:
            result.status = 'error'
            result.error = f"Unexpected error: {str(e)}"
            result.troubleshooting = [
                "This appears to be an internal error",
                "Please report this issue with the error message",
                f"Category: {self.category_name}, URL: {url}"
            ]

        finally:
            # Clean up
            result.execution_time = time.time() - self.start_time
            result.api_calls_made = self.api_calls_made

            if self.session:
                await self.session.close()

        # Validate result has real data (after api_calls_made is set)
        if result.status == 'success':
            try:
                self._validate_real_data(result)
            except AnalysisError as e:
                result.status = 'error'
                result.error = e.message
                result.troubleshooting = e.troubleshooting

        return result

    @abstractmethod
    async def _run_analysis(self, url: str) -> AnalysisResult:
        """
        Implement the actual analysis logic

        This method MUST:
        1. Use real API calls only
        2. Return AnalysisResult with real data
        3. Never simulate or mock data
        4. Raise AnalysisError with clear troubleshooting for failures
        """
        pass

    async def _validate_prerequisites(self, url: str):
        """Validate that we can perform analysis"""

        # Check credentials exist
        if not self.credentials:
            raise AnalysisError(
                "No credentials provided for Sitecore analysis",
                self.category_name,
                url,
                [
                    "Provide Sitecore credentials with --api-key or --username/--password",
                    "Save credentials: smart-sitecore config set-credentials <url>",
                    "Verify the Sitecore instance supports the required APIs"
                ]
            )

        # Check if we need Sitecore access
        if self.requires_sitecore_access:
            if self.credentials.auth_type == 'apikey' and not self.credentials.api_key:
                raise AnalysisError(
                    "API key required but not provided",
                    self.category_name,
                    url,
                    [
                        "Obtain a Sitecore API key from your administrator",
                        "Add it with: --api-key <your-key>",
                        "Or use username/password: --username <user> --password <pass>"
                    ]
                )

            if self.credentials.auth_type == 'basic' and (
                not self.credentials.username or not self.credentials.password
            ):
                raise AnalysisError(
                    "Username/password required but not provided",
                    self.category_name,
                    url,
                    [
                        "Provide Sitecore login credentials",
                        "Add them with: --username <user> --password <pass>",
                        "Or use API key: --api-key <your-key>"
                    ]
                )

    def _validate_real_data(self, result: AnalysisResult):
        """
        Validate that the result contains real data, not mock/simulated data

        This is a critical check that prevents mock data from being presented as real.
        """
        if result.status == 'success':
            # Check that we have meaningful metrics
            if not result.metrics:
                raise AnalysisError(
                    "Analysis succeeded but returned no metrics",
                    self.category_name,
                    "unknown",
                    [
                        "This indicates a problem with the data extraction",
                        "Check that the Sitecore instance is responding correctly",
                        "Verify the API endpoints are accessible"
                    ]
                )

            # Check that data_source is set (tracking where data came from)
            if result.data_source == "unknown":
                result.data_source = "direct_api"  # Default for direct API calls

            # Ensure we made actual API calls (not using cached/mock data)
            if result.api_calls_made == 0 and self.requires_sitecore_access:
                raise AnalysisError(
                    "No API calls were made during analysis",
                    self.category_name,
                    "unknown",
                    [
                        "This suggests the analyzer is not making real API calls",
                        "Check network connectivity to the Sitecore instance",
                        "Verify the endpoints are accessible"
                    ]
                )

    async def _make_graphql_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to Sitecore

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Response data from GraphQL endpoint

        Raises:
            AnalysisError: If request fails
        """
        if not self.session:
            raise AnalysisError(
                "HTTP session not initialized",
                self.category_name,
                self.credentials.url
            )

        graphql_url = self.credentials.get_full_graphql_url()
        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        self.api_calls_made += 1

        try:
            async with self.session.post(graphql_url, json=payload) as response:
                if response.status == 401:
                    raise AnalysisError(
                        "Authentication failed - invalid credentials",
                        self.category_name,
                        self.credentials.url,
                        [
                            "Check that your API key or username/password are correct",
                            "Verify the credentials have sufficient permissions",
                            "Test the credentials in Sitecore admin interface"
                        ]
                    )
                elif response.status == 404:
                    raise AnalysisError(
                        "GraphQL endpoint not found",
                        self.category_name,
                        self.credentials.url,
                        [
                            f"Expected endpoint: {graphql_url}",
                            "Verify GraphQL is enabled on this Sitecore instance",
                            "Check if the URL path is correct for your version"
                        ]
                    )
                elif not response.ok:
                    raise AnalysisError(
                        f"GraphQL request failed: {response.status} {response.reason}",
                        self.category_name,
                        self.credentials.url,
                        [
                            f"HTTP {response.status}: {response.reason}",
                            "Check network connectivity",
                            "Verify the Sitecore instance is running"
                        ]
                    )

                data = await response.json()

                # Check for GraphQL errors
                if 'errors' in data:
                    error_messages = [err.get('message', 'Unknown error') for err in data['errors']]
                    raise AnalysisError(
                        f"GraphQL errors: {'; '.join(error_messages)}",
                        self.category_name,
                        self.credentials.url,
                        [
                            "GraphQL query returned errors",
                            "Check that your query syntax is correct",
                            "Verify you have permissions to access the requested data"
                        ]
                    )

                return data.get('data', {})

        except aiohttp.ClientError as e:
            raise AnalysisError(
                f"Network error: {str(e)}",
                self.category_name,
                self.credentials.url,
                [
                    "Check network connectivity",
                    "Verify the Sitecore URL is accessible",
                    "Check firewall/proxy settings"
                ]
            )

    async def _make_http_request(self, url: str, method: str = 'GET',
                               data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a standard HTTP request

        Args:
            url: Request URL
            method: HTTP method
            data: Optional request data

        Returns:
            Response data

        Raises:
            AnalysisError: If request fails
        """
        if not self.session:
            raise AnalysisError(
                "HTTP session not initialized",
                self.category_name,
                url
            )

        self.api_calls_made += 1

        try:
            async with self.session.request(method, url, json=data) as response:
                if not response.ok:
                    raise AnalysisError(
                        f"HTTP request failed: {response.status} {response.reason}",
                        self.category_name,
                        url,
                        [
                            f"HTTP {response.status}: {response.reason}",
                            "Check the URL is accessible",
                            "Verify any required authentication"
                        ]
                    )

                # Try to parse as JSON, fall back to text
                try:
                    return await response.json()
                except:
                    text = await response.text()
                    return {'content': text, 'status': response.status}

        except aiohttp.ClientError as e:
            raise AnalysisError(
                f"Network error: {str(e)}",
                self.category_name,
                url,
                [
                    "Check network connectivity",
                    "Verify the URL is accessible",
                    "Check firewall/proxy settings"
                ]
            )

    def _calculate_score(self, metrics: Dict[str, Any], scoring_rules: Dict[str, Any]) -> int:
        """
        Calculate category score based on metrics and scoring rules

        Args:
            metrics: Collected metrics
            scoring_rules: Rules for scoring (threshold, penalties, etc.)

        Returns:
            Score between 0-100
        """
        score = 100  # Start with perfect score

        for metric_name, value in metrics.items():
            if metric_name in scoring_rules:
                rule = scoring_rules[metric_name]

                if 'max_penalty' in rule and 'threshold' in rule:
                    # Apply penalty if value exceeds threshold
                    if value > rule['threshold']:
                        penalty = min(rule['max_penalty'],
                                    rule.get('penalty_per_unit', 1) * (value - rule['threshold']))
                        score -= penalty

                elif 'min_score' in rule:
                    # Ensure minimum score for critical metrics
                    if value == 0:
                        score = min(score, rule['min_score'])

        return max(0, min(100, score))


# Utility functions for common operations
async def test_sitecore_connectivity(credentials: SitecoreCredentials) -> Dict[str, Any]:
    """Test basic connectivity to a Sitecore instance"""

    result = {
        'accessible': False,
        'graphql_available': False,
        'authenticated': False,
        'version_info': None,
        'error': None
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout, headers=credentials.get_headers()) as session:

            # Test basic connectivity
            async with session.get(credentials.url) as response:
                result['accessible'] = response.status < 500

            # Test GraphQL endpoint
            graphql_url = credentials.get_full_graphql_url()
            test_query = "query { __typename }"

            async with session.post(graphql_url, json={'query': test_query}) as response:
                if response.status == 401:
                    result['graphql_available'] = True
                    result['error'] = "Authentication required"
                elif response.status == 200:
                    result['graphql_available'] = True
                    result['authenticated'] = True

                    # Try to get version info if available
                    version_query = """
                    query {
                        item(path: "/sitecore/system/Settings/Foundation/Core/Support/Version") {
                            name
                            fields {
                                name
                                value
                            }
                        }
                    }
                    """
                    try:
                        async with session.post(graphql_url, json={'query': version_query}) as ver_response:
                            if ver_response.ok:
                                ver_data = await ver_response.json()
                                result['version_info'] = ver_data.get('data')
                    except:
                        pass

    except Exception as e:
        result['error'] = str(e)

    return result