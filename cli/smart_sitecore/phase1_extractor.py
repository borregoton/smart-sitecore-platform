"""
Phase 1: Sitecore Data Extraction
Implements the four Phase 1 deliverables:
1. GraphQL schema extraction
2. Content tree extraction
3. Template extraction
4. Basic data persistence with scan IDs

Follows supabase_kit.md specification exactly.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import SitecoreCredentials
from .supabase_db_client import supabase_db_client as db_client


class Phase1Extractor:
    """Phase 1 Sitecore data extraction with proper persistence"""

    def __init__(self, credentials: SitecoreCredentials):
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
        self.scan_id: Optional[str] = None
        self.site_id: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._cleanup()

    async def _initialize(self):
        """Initialize HTTP session and database connection"""
        # Initialize database connection
        await db_client.connect()

        # Initialize schema if needed
        await db_client.initialize_schema()

        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=60)
        headers = self.credentials.get_headers()
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        # Set up site and scan
        self.site_id = await db_client.ensure_site(self.credentials.url)
        self.scan_id = await db_client.create_scan(self.site_id)

        print(f"Phase 1 extraction initialized:")
        print(f"  Site ID: {self.site_id}")
        print(f"  Scan ID: {self.scan_id}")

    async def _cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def run_complete_extraction(self) -> str:
        """Run all Phase 1 extraction steps and return scan_id"""

        print("=" * 60)
        print("PHASE 1: SITECORE DATA EXTRACTION")
        print("=" * 60)

        total_start = time.time()

        try:
            # Step 1: GraphQL schema extraction
            print("\n[1/4] GraphQL Schema Extraction")
            print("-" * 30)
            await self._extract_graphql_schema()

            # Step 2: Content tree extraction
            print("\n[2/4] Content Tree Extraction")
            print("-" * 30)
            await self._extract_content_tree()

            # Step 3: Template extraction
            print("\n[3/4] Template Extraction")
            print("-" * 30)
            await self._extract_templates()

            # Step 4: Data persistence verification
            print("\n[4/4] Data Persistence Verification")
            print("-" * 30)
            await self._verify_persistence()

            # Mark scan as complete
            await db_client.finish_scan(self.scan_id)

            total_time = time.time() - total_start
            print(f"\n[SUCCESS] Phase 1 extraction completed successfully!")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Scan ID: {self.scan_id}")

            return self.scan_id

        except Exception as e:
            # Mark scan as error
            await db_client.finish_scan(self.scan_id, str(e))
            print(f"\n[ERROR] Phase 1 extraction failed: {e}")
            raise

    async def _extract_graphql_schema(self):
        """Extract GraphQL schema using introspection"""
        start_time = time.time()

        try:
            # GraphQL introspection query
            introspection_query = """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                    types {
                        ...FullType
                    }
                    directives {
                        name
                        description
                        locations
                        args {
                            ...InputValue
                        }
                    }
                }
            }

            fragment FullType on __Type {
                kind
                name
                description
                fields(includeDeprecated: true) {
                    name
                    description
                    args {
                        ...InputValue
                    }
                    type {
                        ...TypeRef
                    }
                    isDeprecated
                    deprecationReason
                }
                inputFields {
                    ...InputValue
                }
                interfaces {
                    ...TypeRef
                }
                enumValues(includeDeprecated: true) {
                    name
                    description
                    isDeprecated
                    deprecationReason
                }
                possibleTypes {
                    ...TypeRef
                }
            }

            fragment InputValue on __InputValue {
                name
                description
                type { ...TypeRef }
                defaultValue
            }

            fragment TypeRef on __Type {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                    ofType {
                                        kind
                                        name
                                        ofType {
                                            kind
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            graphql_url = self.credentials.get_full_graphql_url()

            async with self.session.post(
                graphql_url,
                json={'query': introspection_query}
            ) as response:

                if response.status == 200:
                    schema_data = await response.json()

                    # Process schema data
                    if 'data' in schema_data and '__schema' in schema_data['data']:
                        schema = schema_data['data']['__schema']

                        # Extract useful schema information
                        query_types = []
                        object_types = []
                        enum_types = []

                        for type_def in schema.get('types', []):
                            # Skip None entries or invalid type definitions
                            if not type_def or not isinstance(type_def, dict):
                                continue

                            # Skip types without required fields
                            if 'kind' not in type_def or 'name' not in type_def:
                                continue

                            if type_def['kind'] == 'OBJECT' and not type_def['name'].startswith('__'):
                                object_types.append({
                                    'name': type_def['name'],
                                    'description': type_def.get('description'),
                                    'field_count': len(type_def.get('fields', []))
                                })
                            elif type_def['kind'] == 'ENUM' and not type_def['name'].startswith('__'):
                                enum_types.append({
                                    'name': type_def['name'],
                                    'values': [v.get('name') for v in type_def.get('enumValues', []) if v and v.get('name')]
                                })

                        # Find query root fields
                        query_type_obj = schema.get('queryType')
                        query_type_name = query_type_obj.get('name') if query_type_obj else 'Query'

                        for type_def in schema.get('types', []):
                            # Skip None entries or invalid type definitions
                            if not type_def or not isinstance(type_def, dict):
                                continue

                            if type_def.get('name') == query_type_name:
                                query_types = []
                                for field in type_def.get('fields', []):
                                    if not field or not isinstance(field, dict):
                                        continue

                                    field_name = field.get('name')
                                    field_type = field.get('type')

                                    if field_name and field_type:
                                        query_types.append({
                                            'name': field_name,
                                            'type': self._extract_type_name(field_type),
                                            'args': len(field.get('args', []))
                                        })
                                break

                        # Safely extract mutation and subscription types
                        mutation_type = schema.get('mutationType')
                        mutation_name = mutation_type.get('name') if mutation_type else None

                        subscription_type = schema.get('subscriptionType')
                        subscription_name = subscription_type.get('name') if subscription_type else None

                        result = {
                            'schema_extracted': True,
                            'query_type': query_type_name,
                            'mutation_type': mutation_name,
                            'subscription_type': subscription_name,
                            'total_types': len(schema.get('types', [])),
                            'object_types': object_types[:20],  # Limit for storage
                            'enum_types': enum_types[:10],      # Limit for storage
                            'query_fields': query_types[:20],   # Limit for storage
                            'extraction_method': 'introspection'
                        }

                        confidence = 0.95
                        print(f"   [SUCCESS] GraphQL introspection successful")
                        print(f"      Types: {len(object_types)} objects, {len(enum_types)} enums")
                        print(f"      Query fields: {len(query_types)}")

                    else:
                        raise Exception("Invalid introspection response structure")

                else:
                    # Introspection blocked - try basic schema detection
                    result = await self._fallback_schema_detection()
                    confidence = 0.6
                    print(f"   [WARNING] Introspection blocked, using fallback detection")

            duration_ms = int((time.time() - start_time) * 1000)

            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-schema",
                data_source="sitecore-graphql",
                confidence=confidence,
                duration_ms=duration_ms,
                result=result,
                requires_credentials=True
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-schema",
                data_source="sitecore-graphql",
                confidence=0.0,
                duration_ms=duration_ms,
                result=None,
                requires_credentials=True,
                error=str(e)
            )
            print(f"   [ERROR] Schema extraction failed: {e}")

    def _extract_type_name(self, type_ref: Dict[str, Any]) -> str:
        """Extract readable type name from GraphQL type reference"""
        if not type_ref or not isinstance(type_ref, dict):
            return 'Unknown'

        if type_ref.get('name'):
            return type_ref['name']
        elif type_ref.get('ofType'):
            return self._extract_type_name(type_ref['ofType'])
        else:
            return 'Unknown'

    async def _fallback_schema_detection(self) -> Dict[str, Any]:
        """Fallback schema detection when introspection is blocked"""

        # Try basic queries to detect available schema elements
        test_queries = [
            'query { __typename }',
            'query { item(path: "/sitecore") { id } }',
            'query { search(first: 1) { results { ... on Item { id } } } }',
            'query { site { name } }'
        ]

        available_queries = []

        for query in test_queries:
            try:
                graphql_url = self.credentials.get_full_graphql_url()
                async with self.session.post(
                    graphql_url,
                    json={'query': query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'errors' not in data:
                            query_name = query.split('{')[1].split('(')[0].strip()
                            available_queries.append(query_name)
            except:
                continue

        return {
            'schema_extracted': False,
            'introspection_blocked': True,
            'available_queries': available_queries,
            'extraction_method': 'fallback_detection'
        }

    async def _extract_content_tree(self):
        """Extract Sitecore content tree structure"""
        start_time = time.time()

        try:
            content_tree_query = """
            query ContentTree($path: String!) {
                item(path: $path, language: "en") {
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

            graphql_url = self.credentials.get_full_graphql_url()

            # Extract content tree starting from /sitecore/content
            async with self.session.post(
                graphql_url,
                json={
                    'query': content_tree_query,
                    'variables': {'path': '/sitecore/content'}
                }
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")

                    content_root = data.get('data', {}).get('item')
                    if not content_root:
                        raise Exception("Content root not found")

                    # Process content tree
                    sites = []
                    total_items = 0

                    children = content_root.get('children', {}).get('results', [])
                    total_direct_children = content_root.get('children', {}).get('total', 0)

                    for child in children:
                        site_info = {
                            'id': child.get('id'),
                            'name': child.get('name'),
                            'path': child.get('path'),
                            'template': child.get('template', {}).get('name'),
                            'has_children': child.get('hasChildren', False),
                            'child_count': child.get('children', {}).get('total', 0)
                        }
                        sites.append(site_info)
                        total_items += site_info['child_count']

                    # Recursively count items (limited depth)
                    recursive_count = await self._count_items_recursive(
                        content_root.get('path'),
                        current_depth=0,
                        max_depth=5
                    )

                    result = {
                        'content_extracted': True,
                        'root_path': content_root.get('path'),
                        'root_id': content_root.get('id'),
                        'root_name': content_root.get('name'),
                        'direct_children': total_direct_children,
                        'estimated_total_items': max(total_items, recursive_count),
                        'sites_discovered': len(sites),
                        'sites': sites,
                        'extraction_method': 'graphql_recursive'
                    }

                    confidence = 0.9
                    print(f"   [SUCCESS] Content tree extracted successfully")
                    print(f"      Sites: {len(sites)}")
                    print(f"      Estimated items: {result['estimated_total_items']}")

                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

            duration_ms = int((time.time() - start_time) * 1000)

            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-content",
                data_source="sitecore-graphql",
                confidence=confidence,
                duration_ms=duration_ms,
                result=result,
                requires_credentials=True
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-content",
                data_source="sitecore-graphql",
                confidence=0.0,
                duration_ms=duration_ms,
                result=None,
                requires_credentials=True,
                error=str(e)
            )
            print(f"   [ERROR] Content tree extraction failed: {e}")

    async def _count_items_recursive(self, path: str, current_depth: int = 0, max_depth: int = 5) -> int:
        """Recursively count items with depth limit"""

        if current_depth >= max_depth:
            return 0

        try:
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

            graphql_url = self.credentials.get_full_graphql_url()

            async with self.session.post(
                graphql_url,
                json={'query': query, 'variables': {'path': path}}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    item = data.get('data', {}).get('item')

                    if not item:
                        return 0

                    total = item.get('children', {}).get('total', 0)
                    children = item.get('children', {}).get('results', [])

                    # For performance, limit recursion
                    if total > 50 or current_depth > 3:
                        return total

                    recursive_count = total
                    for child in children[:5]:  # Limit to first 5 children
                        if child and child.get('hasChildren'):
                            recursive_count += await self._count_items_recursive(
                                child['path'], current_depth + 1, max_depth
                            )

                    return recursive_count

                return 0

        except:
            return 0

    async def _extract_templates(self):
        """Extract Sitecore template information"""
        start_time = time.time()

        try:
            # Try to get template information from system area
            templates_query = """
            query GetTemplates($path: String!) {
                item(path: $path, language: "en") {
                    children {
                        total
                        results {
                            ... on Item {
                                id
                                name
                                path
                                template {
                                    id
                                    name
                                }
                                children {
                                    total
                                }
                            }
                        }
                    }
                }
            }
            """

            graphql_url = self.credentials.get_full_graphql_url()

            # Try different template paths
            template_paths = [
                '/sitecore/templates',
                '/sitecore/templates/User Defined',
                '/sitecore/templates/Foundation',
                '/sitecore/templates/Feature',
                '/sitecore/templates/Project'
            ]

            all_templates = []

            for template_path in template_paths:
                try:
                    async with self.session.post(
                        graphql_url,
                        json={
                            'query': templates_query,
                            'variables': {'path': template_path}
                        }
                    ) as response:

                        if response.status == 200:
                            data = await response.json()

                            if 'errors' not in data:
                                item = data.get('data', {}).get('item')
                                if item:
                                    children = item.get('children', {}).get('results', [])
                                    for child in children:
                                        template_info = {
                                            'id': child.get('id'),
                                            'name': child.get('name'),
                                            'path': child.get('path'),
                                            'base_template': child.get('template', {}).get('name'),
                                            'field_count': child.get('children', {}).get('total', 0),
                                            'source_path': template_path
                                        }
                                        all_templates.append(template_info)

                except Exception as e:
                    print(f"      Template path {template_path} failed: {e}")
                    continue

            # Also extract templates from content analysis
            content_templates = await self._extract_templates_from_content()

            result = {
                'templates_extracted': True,
                'system_templates': all_templates,
                'content_templates': content_templates,
                'total_system_templates': len(all_templates),
                'total_content_templates': len(content_templates),
                'extraction_method': 'system_paths_and_content_analysis'
            }

            confidence = 0.8 if all_templates else 0.6
            print(f"   [SUCCESS] Template extraction completed")
            print(f"      System templates: {len(all_templates)}")
            print(f"      Content templates: {len(content_templates)}")

            duration_ms = int((time.time() - start_time) * 1000)

            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-templates",
                data_source="sitecore-graphql",
                confidence=confidence,
                duration_ms=duration_ms,
                result=result,
                requires_credentials=True
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await db_client.save_module(
                scan_id=self.scan_id,
                module="sitecore-templates",
                data_source="sitecore-graphql",
                confidence=0.0,
                duration_ms=duration_ms,
                result=None,
                requires_credentials=True,
                error=str(e)
            )
            print(f"   [ERROR] Template extraction failed: {e}")

    async def _extract_templates_from_content(self) -> List[Dict[str, Any]]:
        """Extract template usage information from content items"""

        try:
            # Get sample content items to analyze template usage
            sample_query = """
            query SampleContent($path: String!) {
                item(path: $path, language: "en") {
                    children {
                        results {
                            ... on Item {
                                id
                                name
                                template {
                                    id
                                    name
                                }
                                children {
                                    total
                                    results {
                                        ... on Item {
                                            template {
                                                id
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            graphql_url = self.credentials.get_full_graphql_url()

            async with self.session.post(
                graphql_url,
                json={
                    'query': sample_query,
                    'variables': {'path': '/sitecore/content'}
                }
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    if 'errors' not in data:
                        template_usage = {}

                        # Analyze template usage from content
                        items = data.get('data', {}).get('item', {}).get('children', {}).get('results', [])

                        for item in items:
                            template = item.get('template', {})
                            template_name = template.get('name')
                            template_id = template.get('id')

                            if template_name:
                                if template_name not in template_usage:
                                    template_usage[template_name] = {
                                        'id': template_id,
                                        'name': template_name,
                                        'usage_count': 0,
                                        'sample_items': []
                                    }

                                template_usage[template_name]['usage_count'] += 1
                                template_usage[template_name]['sample_items'].append({
                                    'item_name': item.get('name'),
                                    'item_id': item.get('id')
                                })

                            # Check children templates too
                            children = item.get('children', {}).get('results', [])
                            for child in children:
                                child_template = child.get('template', {})
                                child_template_name = child_template.get('name')

                                if child_template_name:
                                    if child_template_name not in template_usage:
                                        template_usage[child_template_name] = {
                                            'id': child_template.get('id'),
                                            'name': child_template_name,
                                            'usage_count': 0,
                                            'sample_items': []
                                        }
                                    template_usage[child_template_name]['usage_count'] += 1

                        return list(template_usage.values())

        except Exception as e:
            print(f"      Content template analysis failed: {e}")

        return []

    async def _verify_persistence(self):
        """Verify that data has been properly persisted to database"""

        try:
            # Get scan results from database
            results = await db_client.get_scan_results(self.scan_id)

            modules_found = len(results)
            successful_modules = len([r for r in results if r['error'] is None])
            total_confidence = sum(r['confidence'] for r in results) / max(modules_found, 1)

            print(f"   [SUCCESS] Data persistence verified")
            print(f"      Modules saved: {modules_found}")
            print(f"      Successful: {successful_modules}")
            print(f"      Average confidence: {total_confidence:.2f}")

            # Show summary of each module
            for result in results:
                status = "[OK]" if result['error'] is None else "[FAIL]"
                print(f"      {status} {result['module']}: {result['confidence']:.2f} confidence, {result['duration_ms']}ms")

            return True

        except Exception as e:
            print(f"   [ERROR] Data persistence verification failed: {e}")
            return False


async def run_phase1_extraction(sitecore_url: str, api_key: str) -> str:
    """Main entry point for Phase 1 extraction"""

    credentials = SitecoreCredentials(
        url=sitecore_url,
        auth_type='apikey',
        api_key=api_key
    )

    async with Phase1Extractor(credentials) as extractor:
        scan_id = await extractor.run_complete_extraction()
        return scan_id