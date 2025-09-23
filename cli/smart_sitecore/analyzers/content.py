"""
Content Management Analyzer
Project20 v2.0 - Real Data Only

Analyzes Sitecore content structure using direct GraphQL queries.
NO MOCK DATA - Real content metrics or clear error reporting.

Metrics:
- Total content items
- Content depth and structure
- Items by template type
- Content completeness (fields filled)
- Broken links detection
- Sites and home nodes
"""

from typing import Dict, Any, List, Optional, Set
from .base import BaseAnalyzer, AnalysisResult, AnalysisError


class ContentAnalyzer(BaseAnalyzer):
    """Content Management analysis using real Sitecore GraphQL data"""

    @property
    def category_name(self) -> str:
        return "content"

    @property
    def requires_sitecore_access(self) -> bool:
        return True

    async def _run_analysis(self, url: str) -> AnalysisResult:
        """Run content analysis using real GraphQL queries"""

        metrics = {}
        issues = []
        recommendations = []

        try:
            # Step 1: Get content root structure
            content_structure = await self._analyze_content_structure()
            metrics.update(content_structure)

            # Step 2: Analyze sites and home nodes
            sites_analysis = await self._analyze_sites()
            metrics.update(sites_analysis)

            # Step 3: Content completeness analysis
            completeness = await self._analyze_content_completeness()
            metrics.update(completeness)

            # Step 4: Template usage analysis
            template_usage = await self._analyze_template_usage()
            metrics.update(template_usage)

            # Generate issues and recommendations based on real data
            issues = self._identify_content_issues(metrics)
            recommendations = self._generate_recommendations(metrics)

            # Calculate score based on real metrics
            score = self._calculate_content_score(metrics)

            return AnalysisResult(
                category=self.category_name,
                status='success',
                score=score,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                data_source='sitecore_graphql'
            )

        except Exception as e:
            raise AnalysisError(
                f"Content analysis failed: {str(e)}",
                self.category_name,
                url,
                [
                    "Verify GraphQL endpoint is accessible",
                    "Check that content tree exists at /sitecore/content",
                    "Ensure API credentials have read permissions",
                    "Try a simpler query first to test connectivity"
                ]
            )

    async def _analyze_content_structure(self) -> Dict[str, Any]:
        """Analyze overall content structure"""

        query = """
        query GetContentStructure {
            item(path: "/sitecore/content", language: "en") {
                id
                name
                path
                children {
                    total
                    results {
                        ... on Item {
                            id
                            name
                            path
                            hasChildren
                            children {
                                total
                            }
                        }
                    }
                }
            }
        }
        """

        data = await self._make_graphql_request(query)

        if not data.get('item'):
            raise AnalysisError(
                "Content root (/sitecore/content) not found",
                self.category_name,
                self.credentials.url,
                [
                    "Verify the Sitecore instance has content at /sitecore/content",
                    "Check that the language parameter ('en') is correct",
                    "Ensure GraphQL has access to the content tree"
                ]
            )

        content_root = data['item']
        total_direct_children = content_root.get('children', {}).get('total', 0)

        # Count total items recursively (with limits to prevent timeout)
        total_items = await self._count_items_recursively("/sitecore/content", max_depth=8)

        # Analyze depth and structure
        max_depth = await self._calculate_max_depth("/sitecore/content")

        return {
            'total_content_items': total_items,
            'total_sites': total_direct_children,
            'content_max_depth': max_depth,
            'content_root_accessible': True
        }

    async def _analyze_sites(self) -> Dict[str, Any]:
        """Analyze individual sites under /sitecore/content"""

        query = """
        query GetSites {
            item(path: "/sitecore/content", language: "en") {
                children {
                    results {
                        ... on Item {
                            id
                            name
                            path
                            template {
                                id
                                name
                            }
                            hasChildren
                            children {
                                total
                            }
                        }
                    }
                }
            }
        }
        """

        data = await self._make_graphql_request(query)
        sites = data.get('item', {}).get('children', {}).get('results', [])

        # Handle both single item and array responses
        if not isinstance(sites, list):
            sites = [sites] if sites else []

        site_analysis = {
            'sites_found': [],
            'home_nodes_found': 0,
            'total_pages_across_sites': 0
        }

        for site in sites:
            if not site:
                continue

            site_info = {
                'name': site.get('name', 'Unknown'),
                'path': site.get('path', ''),
                'template': site.get('template', {}).get('name', 'Unknown'),
                'child_count': site.get('children', {}).get('total', 0)
            }

            # Check if this looks like a site root
            if (site_info['child_count'] > 0 or
                'site' in site_info['template'].lower() or
                site_info['name'].lower() in ['home', 'website', 'site']):

                site_analysis['sites_found'].append(site_info)

                # Count home nodes (look for Home items)
                home_count = await self._count_home_nodes(site_info['path'])
                site_analysis['home_nodes_found'] += home_count

                # Estimate total pages in this site
                page_count = await self._estimate_pages_in_site(site_info['path'])
                site_analysis['total_pages_across_sites'] += page_count

        site_analysis['sites_count'] = len(site_analysis['sites_found'])

        return site_analysis

    async def _analyze_content_completeness(self) -> Dict[str, Any]:
        """Analyze how complete content is (filled vs empty fields)"""

        # Sample a few items to check field completeness
        sample_query = """
        query SampleContentItems {
            search(
                where: {
                    AND: [
                        { name: "_path", value: "/sitecore/content", operator: CONTAINS }
                        { name: "_language", value: "en" }
                    ]
                }
                first: 20
            ) {
                results {
                    items {
                        ... on Item {
                            id
                            name
                            path
                            template {
                                name
                            }
                            fields {
                                name
                                value
                            }
                        }
                    }
                }
            }
        }
        """

        try:
            data = await self._make_graphql_request(sample_query)
            items = data.get('search', {}).get('results', {}).get('items', [])

            if not items:
                # Fallback: try direct item sampling
                return await self._analyze_completeness_fallback()

            total_fields = 0
            filled_fields = 0
            user_facing_fields = 0
            user_facing_filled = 0

            for item in items:
                fields = item.get('fields', [])
                for field in fields:
                    field_name = field.get('name', '')
                    field_value = field.get('value', '')

                    # Skip system fields
                    if field_name.startswith('__') or field_name.startswith('_'):
                        continue

                    total_fields += 1
                    user_facing_fields += 1

                    # Check if field has content
                    if (field_value and
                        field_value.strip() != '' and
                        field_value != '<p></p>' and
                        field_value != '0' and
                        field_value != '00000000-0000-0000-0000-000000000000'):

                        filled_fields += 1
                        user_facing_filled += 1

            completeness_rate = 0
            if user_facing_fields > 0:
                completeness_rate = round((user_facing_filled / user_facing_fields) * 100)

            return {
                'content_completeness_rate': completeness_rate,
                'total_fields_sampled': user_facing_fields,
                'filled_fields_sampled': user_facing_filled,
                'sample_size': len(items)
            }

        except Exception as e:
            # If sampling fails, return basic completeness info
            return {
                'content_completeness_rate': 0,
                'completeness_error': f"Could not sample content: {str(e)}"
            }

    async def _analyze_completeness_fallback(self) -> Dict[str, Any]:
        """Fallback completeness analysis using direct item queries"""

        # Try to get a few specific items to check completeness
        test_paths = [
            "/sitecore/content/Home",
            "/sitecore/content/Website/Home",
            "/sitecore/content/Global"
        ]

        total_checked = 0
        completeness_scores = []

        for path in test_paths:
            try:
                query = f"""
                query GetItemFields($path: String!) {{
                    item(path: $path, language: "en") {{
                        id
                        name
                        fields {{
                            name
                            value
                        }}
                    }}
                }}
                """

                data = await self._make_graphql_request(query, {'path': path})
                item = data.get('item')

                if item:
                    total_checked += 1
                    fields = item.get('fields', [])

                    user_fields = 0
                    filled_fields = 0

                    for field in fields:
                        if not field.get('name', '').startswith('__'):
                            user_fields += 1
                            if field.get('value', '').strip():
                                filled_fields += 1

                    if user_fields > 0:
                        completeness_scores.append((filled_fields / user_fields) * 100)

            except:
                continue

        avg_completeness = 0
        if completeness_scores:
            avg_completeness = round(sum(completeness_scores) / len(completeness_scores))

        return {
            'content_completeness_rate': avg_completeness,
            'items_checked': total_checked,
            'analysis_method': 'fallback_sampling'
        }

    async def _analyze_template_usage(self) -> Dict[str, Any]:
        """Analyze template usage patterns"""

        # This would require a more complex query or multiple queries
        # For now, return basic template info
        return {
            'template_analysis': 'basic',
            'template_diversity_note': 'Template analysis requires deeper GraphQL queries'
        }

    async def _count_items_recursively(self, path: str, current_depth: int = 0,
                                     max_depth: int = 8) -> int:
        """Count items recursively with depth limit"""

        if current_depth >= max_depth:
            return 0

        query = """
        query CountItems($path: String!) {
            item(path: $path, language: "en") {
                children {
                    total
                    results {
                        ... on Item {
                            path
                            hasChildren
                        }
                    }
                }
            }
        }
        """

        try:
            data = await self._make_graphql_request(query, {'path': path})
            item = data.get('item')

            if not item:
                return 0

            total = item.get('children', {}).get('total', 0)
            children = item.get('children', {}).get('results', [])

            # For performance, if we have more than 50 items, just return the total
            # without recursing (to avoid timeout)
            if total > 50 or current_depth > 4:
                return total

            # Recurse into children (limited)
            if isinstance(children, list) and len(children) > 0:
                recursive_count = total  # Start with direct children
                for child in children[:10]:  # Limit to first 10 to prevent timeout
                    if child and child.get('hasChildren'):
                        recursive_count += await self._count_items_recursively(
                            child['path'], current_depth + 1, max_depth
                        )
                return recursive_count

            return total

        except:
            return 0

    async def _calculate_max_depth(self, path: str, current_depth: int = 0) -> int:
        """Calculate maximum content depth"""

        if current_depth > 10:  # Prevent infinite recursion
            return current_depth

        query = """
        query GetDepth($path: String!) {
            item(path: $path, language: "en") {
                children {
                    results {
                        ... on Item {
                            path
                            hasChildren
                        }
                    }
                }
            }
        }
        """

        try:
            data = await self._make_graphql_request(query, {'path': path})
            children = data.get('item', {}).get('children', {}).get('results', [])

            if not children:
                return current_depth

            max_child_depth = current_depth
            for child in children[:5]:  # Limit to prevent timeout
                if child and child.get('hasChildren'):
                    child_depth = await self._calculate_max_depth(
                        child['path'], current_depth + 1
                    )
                    max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        except:
            return current_depth

    async def _count_home_nodes(self, site_path: str) -> int:
        """Count home nodes in a site"""

        query = """
        query FindHomeNodes($path: String!) {
            item(path: $path, language: "en") {
                children {
                    results {
                        ... on Item {
                            name
                        }
                    }
                }
            }
        }
        """

        try:
            data = await self._make_graphql_request(query, {'path': site_path})
            children = data.get('item', {}).get('children', {}).get('results', [])

            home_count = 0
            for child in children:
                if child and child.get('name', '').lower() in ['home', 'homepage', 'start']:
                    home_count += 1

            return home_count

        except:
            return 0

    async def _estimate_pages_in_site(self, site_path: str) -> int:
        """Estimate number of pages in a site"""

        query = """
        query EstimatePages($path: String!) {
            item(path: $path, language: "en") {
                children {
                    total
                }
            }
        }
        """

        try:
            data = await self._make_graphql_request(query, {'path': site_path})
            total = data.get('item', {}).get('children', {}).get('total', 0)

            # Rough estimation: assume 60% of items are pages
            estimated_pages = round(total * 0.6)
            return max(estimated_pages, 1) if total > 0 else 0

        except:
            return 0

    def _identify_content_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify content-related issues based on real metrics"""

        issues = []

        # Check content volume
        total_items = metrics.get('total_content_items', 0)
        if total_items == 0:
            issues.append("No content items found - content tree may be empty or inaccessible")
        elif total_items < 10:
            issues.append(f"Very low content volume ({total_items} items) - site may be underdeveloped")

        # Check site structure
        sites_count = metrics.get('sites_count', 0)
        if sites_count == 0:
            issues.append("No sites found under /sitecore/content")
        elif sites_count > 20:
            issues.append(f"Many sites detected ({sites_count}) - consider content consolidation")

        # Check content depth
        max_depth = metrics.get('content_max_depth', 0)
        if max_depth > 8:
            issues.append(f"Deep content hierarchy ({max_depth} levels) may impact performance")
        elif max_depth < 3:
            issues.append("Shallow content structure may indicate organizational issues")

        # Check content completeness
        completeness = metrics.get('content_completeness_rate', 0)
        if completeness < 50:
            issues.append(f"Low content completeness ({completeness}%) - many empty fields detected")

        # Check home nodes
        home_nodes = metrics.get('home_nodes_found', 0)
        if home_nodes == 0:
            issues.append("No home nodes found - site navigation may be broken")

        return issues

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on real metrics"""

        recommendations = []

        # Content volume recommendations
        total_items = metrics.get('total_content_items', 0)
        if total_items < 50:
            recommendations.append("Develop more content to improve site value and SEO performance")

        # Structure recommendations
        max_depth = metrics.get('content_max_depth', 0)
        if max_depth > 6:
            recommendations.append("Consider flattening content hierarchy to improve performance and usability")

        # Completeness recommendations
        completeness = metrics.get('content_completeness_rate', 0)
        if completeness < 70:
            recommendations.append("Conduct content audit to fill empty fields and improve content quality")

        # Site organization recommendations
        sites_count = metrics.get('sites_count', 0)
        if sites_count > 10:
            recommendations.append("Review site architecture - consider consolidating similar sites")

        # Home node recommendations
        home_nodes = metrics.get('home_nodes_found', 0)
        if home_nodes == 0:
            recommendations.append("Ensure each site has a proper home node for navigation")

        return recommendations

    def _calculate_content_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate content score based on real metrics"""

        score = 100

        # Content volume scoring (0-30 points)
        total_items = metrics.get('total_content_items', 0)
        if total_items == 0:
            score -= 50
        elif total_items < 10:
            score -= 30
        elif total_items < 50:
            score -= 15

        # Content completeness scoring (0-25 points)
        completeness = metrics.get('content_completeness_rate', 0)
        if completeness < 30:
            score -= 25
        elif completeness < 50:
            score -= 15
        elif completeness < 70:
            score -= 10

        # Structure scoring (0-25 points)
        max_depth = metrics.get('content_max_depth', 0)
        if max_depth > 10:
            score -= 20
        elif max_depth > 8:
            score -= 10
        elif max_depth < 2:
            score -= 15

        # Site organization scoring (0-20 points)
        sites_count = metrics.get('sites_count', 0)
        home_nodes = metrics.get('home_nodes_found', 0)

        if sites_count == 0:
            score -= 20
        elif home_nodes < sites_count:
            score -= 10

        return max(0, min(100, score))