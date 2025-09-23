#!/usr/bin/env python3
"""
Debug GraphQL Schema Extraction Issue
Reproduce and fix the 'NoneType' error in schema extraction
"""

import asyncio
import sys
import os
import aiohttp
import json

# Add the cli directory to the path so we can import modules
sys.path.insert(0, 'cli')

from smart_sitecore.config import SitecoreCredentials


async def debug_graphql_schema():
    """Debug the GraphQL schema extraction to find the NoneType error"""

    print("DEBUG: GraphQL Schema Extraction")
    print("=" * 40)

    # Known working Sitecore endpoint
    sitecore_url = "https://cm-qa-sc103.kajoo.ca"
    api_key = "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}"

    credentials = SitecoreCredentials(
        url=sitecore_url,
        auth_type='apikey',
        api_key=api_key
    )

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

    timeout = aiohttp.ClientTimeout(total=60)
    headers = credentials.get_headers()

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:

        graphql_url = credentials.get_full_graphql_url()
        print(f"Testing GraphQL URL: {graphql_url}")
        print(f"Headers: {headers}")

        try:
            async with session.post(
                graphql_url,
                json={'query': introspection_query}
            ) as response:

                print(f"Response Status: {response.status}")
                print(f"Response Headers: {dict(response.headers)}")

                if response.status == 200:
                    schema_data = await response.json()
                    print(f"Response received successfully")

                    # Debug the response structure
                    print(f"\\nDEBUG: Response keys: {list(schema_data.keys())}")

                    if 'data' in schema_data:
                        print(f"Data keys: {list(schema_data['data'].keys())}")

                        if '__schema' in schema_data['data']:
                            schema = schema_data['data']['__schema']
                            print(f"Schema keys: {list(schema.keys())}")

                            # Debug types array
                            types = schema.get('types', [])
                            print(f"\\nDEBUG: Types count: {len(types)}")

                            # Check for None entries in types
                            none_count = 0
                            for i, type_def in enumerate(types):
                                if type_def is None:
                                    none_count += 1
                                    print(f"  WARNING: Type at index {i} is None")
                                elif not isinstance(type_def, dict):
                                    print(f"  WARNING: Type at index {i} is not a dict: {type(type_def)}")
                                else:
                                    # Check for missing required fields
                                    if 'kind' not in type_def:
                                        print(f"  WARNING: Type at index {i} missing 'kind': {type_def}")
                                    if 'name' not in type_def:
                                        print(f"  WARNING: Type at index {i} missing 'name': {type_def}")

                            print(f"Found {none_count} None entries in types array")

                            # Test the problematic code path
                            print(f"\\nDEBUG: Testing schema processing...")

                            # Find query root fields - this is where the error likely occurs
                            query_type_name = schema.get('queryType', {}).get('name', 'Query')
                            print(f"Query type name: {query_type_name}")

                            for i, type_def in enumerate(types):
                                if type_def is None:
                                    print(f"  Skipping None type at index {i}")
                                    continue

                                if not isinstance(type_def, dict):
                                    print(f"  Skipping non-dict type at index {i}")
                                    continue

                                if 'name' not in type_def:
                                    print(f"  Skipping type without name at index {i}")
                                    continue

                                if type_def['name'] == query_type_name:
                                    print(f"  Found Query type definition")

                                    fields = type_def.get('fields', [])
                                    print(f"  Query has {len(fields)} fields")

                                    for j, field in enumerate(fields):
                                        if field is None:
                                            print(f"    WARNING: Field at index {j} is None")
                                            continue

                                        if not isinstance(field, dict):
                                            print(f"    WARNING: Field at index {j} is not dict: {type(field)}")
                                            continue

                                        field_name = field.get('name', 'UNKNOWN')
                                        field_type = field.get('type')

                                        if field_type is None:
                                            print(f"    WARNING: Field '{field_name}' has None type")
                                        else:
                                            # This is where the error occurs - calling _extract_type_name with None
                                            try:
                                                type_name = extract_type_name_safe(field_type)
                                                print(f"    Field '{field_name}': {type_name}")
                                            except Exception as e:
                                                print(f"    ERROR extracting type for field '{field_name}': {e}")
                                                print(f"    Field type was: {field_type}")

                                    break

                        else:
                            print(f"No '__schema' in data")
                    else:
                        print(f"No 'data' in response")

                    # Check for errors
                    if 'errors' in schema_data:
                        print(f"\\nGraphQL Errors: {schema_data['errors']}")

                else:
                    text = await response.text()
                    print(f"HTTP Error {response.status}: {text[:500]}")

        except Exception as e:
            print(f"Request failed: {e}")
            import traceback
            traceback.print_exc()


def extract_type_name_safe(type_ref):
    """Safe version of _extract_type_name with better error handling"""
    if type_ref is None:
        return 'NULL_TYPE'

    if not isinstance(type_ref, dict):
        return f'INVALID_TYPE({type(type_ref).__name__})'

    if type_ref.get('name'):
        return type_ref['name']
    elif type_ref.get('ofType'):
        return extract_type_name_safe(type_ref['ofType'])
    else:
        return 'Unknown'


if __name__ == "__main__":
    print("Starting GraphQL schema extraction debug...")
    asyncio.run(debug_graphql_schema())