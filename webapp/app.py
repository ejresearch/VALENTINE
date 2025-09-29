#!/usr/bin/env python3
"""
Screenplay Formatter Web App
A simple local web interface for the screenplay formatter CLI tool.
"""

import os
import sys
import json
import tempfile
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

# Add the parent directory to Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.screenplay_formatter.parser import ScreenplayParser
from src.screenplay_formatter.formatter import TextFormatter, DocxFormatter, PdfFormatter
from src.screenplay_formatter.validator import ScreenplayValidator
from src.screenplay_formatter.config import config_manager

try:
    from src.screenplay_formatter.llm_corrector import LLMCorrector
    from src.screenplay_formatter.fix_engine import FixEngine
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Global storage for processing results
processing_results = {}

@app.route('/')
def index():
    """Serve the main web interface."""
    response = send_from_directory('.', 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/logo.png')
def logo():
    """Serve the logo image."""
    return send_from_directory('.', 'logo.png')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify({
        'has_api_key': config_manager.has_api_key(),
        'llm_available': LLM_AVAILABLE,
        'default_confidence': config_manager.get_default_confidence(),
        'default_model': config_manager.get_default_model()
    })

@app.route('/api/config/api-key', methods=['POST'])
def save_api_key():
    """Save API key configuration."""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()

    if api_key:
        config_manager.set_openai_api_key(api_key)
        return jsonify({'success': True, 'message': 'API key saved successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid API key'}), 400

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.lower().endswith(('.txt', '.md')):
        try:
            # Read file content
            content = file.read().decode('utf-8')

            # Generate a session ID for this upload
            import uuid
            session_id = str(uuid.uuid4())

            # Store the content temporarily
            temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}_input.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Quick validation to give feedback
            parser = ScreenplayParser()
            elements = parser.parse(content)
            validator = ScreenplayValidator()
            report = validator.validate(elements)

            return jsonify({
                'session_id': session_id,
                'filename': secure_filename(file.filename),
                'size': len(content),
                'elements_count': len(elements),
                'validation': {
                    'passed': report.passed,
                    'total_errors': report.total_errors,
                    'errors_by_type': report.errors_by_type
                }
            })

        except Exception as e:
            return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type. Please upload a .txt or .md file.'}), 400

@app.route('/api/process', methods=['POST'])
def process_screenplay():
    """Process the uploaded screenplay."""
    data = request.get_json()
    session_id = data.get('session_id')
    format_mode = data.get('format_mode', 'format')
    output_formats = data.get('output_formats', ['txt'])
    ai_settings = data.get('ai_settings', {})

    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400

    # Read the uploaded file
    input_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}_input.txt')
    if not os.path.exists(input_file):
        return jsonify({'error': 'Session expired or file not found'}), 404

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the content
        parser = ScreenplayParser()
        elements = parser.parse(content)

        results = {'session_id': session_id, 'files': [], 'summary': {}}

        # Choose processing method based on format_mode
        if format_mode == 'ai-fix' and LLM_AVAILABLE:
            results.update(process_with_ai(content, elements, session_id, output_formats, ai_settings))
        elif format_mode == 'smart':
            results.update(process_smart_format(content, elements, session_id, output_formats, ai_settings))
        else:
            results.update(process_standard_format(elements, session_id, output_formats))

        # Store results for download
        processing_results[session_id] = results

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

def process_standard_format(elements, session_id, output_formats):
    """Process with standard formatting."""
    results = {'files': [], 'summary': {'method': 'Standard Formatting', 'elements_processed': len(elements)}}

    base_name = f'{session_id}_formatted'

    for format_type in output_formats:
        if format_type == 'txt':
            formatter = TextFormatter()
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{base_name}.txt')
            formatter.format(elements, output_file)
            results['files'].append({'format': 'txt', 'path': output_file, 'name': 'formatted_screenplay.txt'})

        elif format_type == 'docx':
            formatter = DocxFormatter()
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{base_name}.docx')
            formatter.format(elements, output_file)
            results['files'].append({'format': 'docx', 'path': output_file, 'name': 'formatted_screenplay.docx'})

        elif format_type == 'pdf':
            formatter = PdfFormatter()
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{base_name}.pdf')
            formatter.format(elements, output_file)
            results['files'].append({'format': 'pdf', 'path': output_file, 'name': 'formatted_screenplay.pdf'})

    return results

def process_with_ai(content, elements, session_id, output_formats, ai_settings):
    """Process with AI correction."""
    if not LLM_AVAILABLE:
        raise Exception("AI processing not available. Please install OpenAI library.")

    try:
        # Initialize AI corrector
        corrector = LLMCorrector(
            api_key=config_manager.get_openai_api_key(),
            min_confidence=ai_settings.get('confidence', 0.8)
        )

        # Initialize fix engine
        engine = FixEngine(
            llm_corrector=corrector,
            dry_run=ai_settings.get('dry_run', False)
        )

        # Run AI correction
        fix_result = engine.fix_screenplay(content)

        results = {
            'files': [],
            'summary': {
                'method': 'AI-Powered Correction',
                'original_errors': fix_result.original_errors,
                'remaining_errors': fix_result.remaining_errors,
                'applied_fixes': fix_result.applied_fixes,
                'suggested_fixes': fix_result.suggested_fixes,
                'dry_run': ai_settings.get('dry_run', False)
            }
        }

        # Generate audit log if requested
        if ai_settings.get('generate_audit', False):
            audit_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}_audit.json')
            engine.export_audit_log(fix_result, audit_file)
            results['files'].append({'format': 'json', 'path': audit_file, 'name': 'correction_audit.json'})

        # If not dry run, format the corrected content
        if not ai_settings.get('dry_run', False) and fix_result.applied_fixes > 0:
            # For now, use original elements since we'd need to implement text reconstruction
            # In a full implementation, this would use the corrected text
            format_results = process_standard_format(elements, session_id, output_formats)
            results['files'].extend(format_results['files'])
        else:
            # Dry run or no fixes - just format original
            format_results = process_standard_format(elements, session_id, output_formats)
            results['files'].extend(format_results['files'])

        return results

    except Exception as e:
        if "API key" in str(e):
            raise Exception("OpenAI API key not configured. Please set your API key in the settings.")
        raise e

def process_smart_format(content, elements, session_id, output_formats, ai_settings):
    """Process with smart format (auto-detect)."""
    # Validate first to decide approach
    validator = ScreenplayValidator()
    report = validator.validate(elements)

    if report.passed:
        # Use standard formatting
        results = process_standard_format(elements, session_id, output_formats)
        results['summary']['method'] = 'Smart Format (Standard)'
        results['summary']['reason'] = 'Screenplay passed validation - used standard formatting'
    else:
        # Use AI correction if available
        if LLM_AVAILABLE and config_manager.has_api_key():
            results = process_with_ai(content, elements, session_id, output_formats, ai_settings)
            results['summary']['method'] = 'Smart Format (AI-Corrected)'
            results['summary']['reason'] = f'Found {report.total_errors} errors - used AI correction'
        else:
            # Fall back to standard formatting
            results = process_standard_format(elements, session_id, output_formats)
            results['summary']['method'] = 'Smart Format (Standard)'
            results['summary']['reason'] = 'Errors found but AI not available - used standard formatting'

    return results

@app.route('/api/download/<session_id>')
def download_all(session_id):
    """Download all generated files as a ZIP."""
    if session_id not in processing_results:
        return jsonify({'error': 'Results not found'}), 404

    results = processing_results[session_id]
    files = results['files']

    if not files:
        return jsonify({'error': 'No files to download'}), 404

    # Create a ZIP file
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}_all_formats.zip')

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_info in files:
            if os.path.exists(file_info['path']):
                zipf.write(file_info['path'], file_info['name'])

    return send_file(zip_path, as_attachment=True, download_name='screenplay_formatted.zip')

@app.route('/api/download/<session_id>/<format_type>')
def download_format(session_id, format_type):
    """Download a specific format."""
    if session_id not in processing_results:
        return jsonify({'error': 'Results not found'}), 404

    results = processing_results[session_id]

    for file_info in results['files']:
        if file_info['format'] == format_type:
            return send_file(file_info['path'], as_attachment=True, download_name=file_info['name'])

    return jsonify({'error': f'Format {format_type} not found'}), 404

@app.route('/api/status')
def status():
    """Get application status."""
    return jsonify({
        'status': 'running',
        'llm_available': LLM_AVAILABLE,
        'has_api_key': config_manager.has_api_key(),
        'version': '1.0.0'
    })

def cleanup_old_files():
    """Clean up old temporary files."""
    import time
    import glob

    temp_dir = app.config['UPLOAD_FOLDER']
    cutoff_time = time.time() - 3600  # 1 hour ago

    for pattern in ['*_input.txt', '*_formatted.*', '*_audit.json', '*_all_formats.zip']:
        for file_path in glob.glob(os.path.join(temp_dir, pattern)):
            try:
                if os.path.getctime(file_path) < cutoff_time:
                    os.remove(file_path)
            except OSError:
                pass  # Ignore errors during cleanup

if __name__ == '__main__':
    print("🎬 Screenplay Formatter Web App")
    print("=" * 50)
    print("Starting local web server...")
    print("Open your browser to: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    # Clean up old files on startup
    cleanup_old_files()

    # Run the Flask app
    app.run(host='127.0.0.1', port=5001, debug=False)