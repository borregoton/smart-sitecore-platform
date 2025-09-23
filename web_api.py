#!/usr/bin/env python3
"""
Smart Sitecore Analysis Engine - Web API
=========================================
Flask-based REST API for Sitecore analysis functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import traceback
from datetime import datetime
import json

# Import analysis modules
try:
    from cli.smart_sitecore.analyzers.content_enhanced import ContentAnalyzer
    from cli.smart_sitecore.supabase_client_v2 import SupabaseClient
    from cli.smart_sitecore.config import Config
    ANALYZERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import analysis modules: {e}")
    ANALYZERS_AVAILABLE = False

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
config = None
supabase_client = None

def initialize_services():
    """Initialize Supabase client and configuration"""
    global config, supabase_client

    try:
        config = Config()
        supabase_client = SupabaseClient()
        logger.info("Services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Basic health check
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'analyzers': ANALYZERS_AVAILABLE,
                'database': supabase_client is not None if supabase_client else False
            }
        }

        # Test database connection if available
        if supabase_client:
            try:
                # Simple query to test connection
                result = supabase_client.table('customers').select('id').limit(1).execute()
                status['services']['database'] = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
                status['services']['database'] = False

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_sitecore():
    """Main analysis endpoint"""
    if not ANALYZERS_AVAILABLE:
        return jsonify({
            'error': 'Analysis modules not available',
            'details': 'Required analyzer modules could not be imported'
        }), 503

    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Required parameters
        site_url = data.get('site_url')
        if not site_url:
            return jsonify({'error': 'site_url is required'}), 400

        # Optional parameters
        customer_id = data.get('customer_id')
        site_id = data.get('site_id')
        analysis_type = data.get('analysis_type', 'full')

        logger.info(f"Starting analysis for {site_url}")

        # Initialize analyzer
        analyzer = ContentAnalyzer()

        # Perform analysis based on type
        if analysis_type == 'content':
            result = analyzer.analyze_content(site_url)
        elif analysis_type == 'schema':
            result = analyzer.analyze_schema(site_url)
        elif analysis_type == 'full':
            result = analyzer.analyze_full(site_url)
        else:
            return jsonify({'error': f'Invalid analysis_type: {analysis_type}'}), 400

        # Store results if customer/site IDs provided
        if customer_id and site_id and supabase_client:
            try:
                scan_data = {
                    'customer_id': customer_id,
                    'site_id': site_id,
                    'scan_type': analysis_type,
                    'status': 'completed',
                    'results': result,
                    'created_at': datetime.utcnow().isoformat()
                }

                supabase_client.table('scans').insert(scan_data).execute()
                logger.info(f"Analysis results stored for customer {customer_id}, site {site_id}")

            except Exception as e:
                logger.warning(f"Failed to store analysis results: {e}")

        # Return results
        response = {
            'status': 'success',
            'analysis_type': analysis_type,
            'site_url': site_url,
            'timestamp': datetime.utcnow().isoformat(),
            'results': result
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        logger.error(traceback.format_exc())

        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/customers', methods=['GET'])
def list_customers():
    """List all customers"""
    if not supabase_client:
        return jsonify({'error': 'Database not available'}), 503

    try:
        result = supabase_client.table('customers').select('*').execute()
        return jsonify({
            'status': 'success',
            'customers': result.data
        }), 200

    except Exception as e:
        logger.error(f"Failed to list customers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<customer_id>/sites', methods=['GET'])
def list_customer_sites(customer_id):
    """List sites for a specific customer"""
    if not supabase_client:
        return jsonify({'error': 'Database not available'}), 503

    try:
        result = supabase_client.table('customer_sites').select('*').eq('customer_id', customer_id).execute()
        return jsonify({
            'status': 'success',
            'sites': result.data
        }), 200

    except Exception as e:
        logger.error(f"Failed to list sites for customer {customer_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<site_id>/scans', methods=['GET'])
def list_site_scans(site_id):
    """List scans for a specific site"""
    if not supabase_client:
        return jsonify({'error': 'Database not available'}), 503

    try:
        result = supabase_client.table('scans').select('*').eq('site_id', site_id).order('created_at', desc=True).execute()
        return jsonify({
            'status': 'success',
            'scans': result.data
        }), 200

    except Exception as e:
        logger.error(f"Failed to list scans for site {site_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scans/<scan_id>', methods=['GET'])
def get_scan_details(scan_id):
    """Get detailed scan results"""
    if not supabase_client:
        return jsonify({'error': 'Database not available'}), 503

    try:
        result = supabase_client.table('scans').select('*').eq('id', scan_id).single().execute()
        return jsonify({
            'status': 'success',
            'scan': result.data
        }), 200

    except Exception as e:
        logger.error(f"Failed to get scan {scan_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API status and capabilities"""
    return jsonify({
        'api_version': '1.0.0',
        'status': 'operational',
        'capabilities': {
            'analysis': ANALYZERS_AVAILABLE,
            'storage': supabase_client is not None,
            'multi_customer': True
        },
        'endpoints': [
            'GET /health',
            'POST /api/analyze',
            'GET /api/customers',
            'GET /api/customers/<customer_id>/sites',
            'GET /api/sites/<site_id>/scans',
            'GET /api/scans/<scan_id>',
            'GET /api/status'
        ]
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Initialize services
    if not initialize_services():
        logger.warning("Some services failed to initialize, API will have limited functionality")

    # Run the app
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'

    logger.info(f"Starting Smart Sitecore Analysis API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)