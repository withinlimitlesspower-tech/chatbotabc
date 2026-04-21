"""
app.py - Main application file
Project: Project
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

# Third-party imports
try:
    from flask import Flask, request, jsonify, render_template, abort
    from flask_cors import CORS
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages: flask, flask-cors, requests, python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables
CONFIG_FILE = 'config.json'
DATA_FILE = 'data.json'

def load_config() -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Returns:
        Dict containing configuration data
    """
    default_config = {
        "api_endpoint": "https://api.example.com",
        "timeout": 30,
        "retry_attempts": 3,
        "features": {
            "enable_cache": True,
            "enable_logging": True
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded successfully")
                return {**default_config, **config}  # Merge with defaults
        else:
            logger.warning(f"Config file {CONFIG_FILE} not found, using defaults")
            return default_config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return default_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return default_config

def save_data(data: Dict[str, Any]) -> bool:
    """
    Save data to JSON file.
    
    Args:
        data: Dictionary to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False

def load_data() -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Returns:
        Dict containing loaded data
    """
    default_data = {
        "items": [],
        "last_updated": None,
        "metadata": {}
    }
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info("Data loaded successfully")
                return data
        else:
            logger.info(f"Data file {DATA_FILE} not found, returning empty data")
            return default_data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing data file: {e}")
        return default_data
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return default_data

def validate_input(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
    """
    Validate input data.
    
    Args:
        data: Input data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Input must be a JSON object"
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""

@app.route('/')
def index():
    """
    Home page route.
    
    Returns:
        Rendered HTML template
    """
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return "Welcome to Project API", 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Project API",
            "version": "1.0.0"
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Get current configuration.
    
    Returns:
        JSON response with configuration
    """
    try:
        config = load_config()
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({"error": "Failed to load configuration"}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Get stored data.
    
    Returns:
        JSON response with data
    """
    try:
        data = load_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error getting data: {e}")
        return jsonify({"error": "Failed to load data"}), 500

@app.route('/api/data', methods=['POST'])
def add_data():
    """
    Add new data.
    
    Returns:
        JSON response with operation result
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        
        # Validate input
        is_valid, error_msg = validate_input(data, ["name", "value"])
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Load existing data
        existing_data = load_data()
        
        # Add new item with timestamp
        new_item = {
            **data,
            "id": len(existing_data["items"]) + 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        existing_data["items"].append(new_item)
        existing_data["last_updated"] = datetime.utcnow().isoformat()
        
        # Save updated data
        if save_data(existing_data):
            return jsonify({
                "message": "Data added successfully",
                "id": new_item["id"],
                "item": new_item
            }), 201
        else:
            return jsonify({"error": "Failed to save data"}), 500
            
    except Exception as e:
        logger.error(f"Error adding data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/data/<int:item_id>', methods=['GET'])
def get_data_item(item_id: int):
    """
    Get specific data item by ID.
    
    Args:
        item_id: Item ID
        
    Returns:
        JSON response with item data
    """
    try:
        data = load_data()
        
        # Find item by ID
        item = next((item for item in data["items"] if item.get("id") == item_id), None)
        
        if item:
            return jsonify(item), 200
        else:
            return jsonify({"error": f"Item with ID {item_id} not found"}), 404
            
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/data/<int:item_id>', methods=['PUT'])
def update_data_item(item_id: int):
    """
    Update specific data item.
    
    Args:
        item_id: Item ID
        
    Returns:
        JSON response with operation result
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        update_data = request.get_json()
        
        # Load existing data
        data = load_data()
        
        # Find item index
        item_index = next((i for i, item in enumerate(data["items"]) 
                          if item.get("id") == item_id), None)