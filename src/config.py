# Configuration for AI Supplier Agent
# API keys, Supabase URL, folder paths
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://YOUR_PROJECT.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_KEY")

# OpenAI Configuration  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# App Configuration
PDF_FOLDER = "pdfs"
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "true").lower() == "true"

# Database Table Names
TABLE_SUPPLIERS = "suppliers"
TABLE_PRODUCTS = "products" 
TABLE_DOCUMENTS = "documents"
TABLE_EXTRACTIONS = "extractions"

# Check configuration status
def get_config_status():
    """Get configuration status for debugging"""
    return {
        "supabase_configured": SUPABASE_URL != "https://YOUR_PROJECT.supabase.co",
        "openai_configured": OPENAI_API_KEY != "YOUR_OPENAI_API_KEY",
        "database_enabled": DATABASE_ENABLED,
        "has_env_file": os.path.exists(".env")
    }

# Instructions:
# 1. Get OpenAI API key from: https://platform.openai.com/api-keys
# 2. Replace YOUR_OPENAI_API_KEY with your actual API key
# 3. Get Supabase details from your Supabase project dashboard
# 4. Replace the placeholders with your actual values
