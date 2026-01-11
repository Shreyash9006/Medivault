import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY', 'medivault-hackathon-secret-key-2024')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database/medivault.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # OpenAI Model Selection
    GPT_MODEL = 'gpt-4-turbo-preview'  # For medical summarization
    WHISPER_MODEL = 'whisper-1'  # For voice transcription
    EMBEDDING_MODEL = 'text-embedding-3-small'  # For semantic search
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}
    
    # Health ID Configuration
    HEALTH_ID_PREFIX = 'MV'  # MediVault prefix
    HEALTH_ID_LENGTH = 8  # Total length including prefix
    
    # Emergency Mode Configuration
    EMERGENCY_SUMMARY_MAX_TOKENS = 150  # Keep emergency summaries concise
    EMERGENCY_TIMEOUT_SECONDS = 15  # Target response time
    
    # AI Prompt Templates
    EMERGENCY_SYSTEM_PROMPT = """You are a clinical medical summarization assistant for emergency situations.
You extract factual information only from patient medical records.
You do not diagnose, prescribe, or speculate.
If information is missing, state "Not documented".
Keep responses under 70 words total."""
    
    EMERGENCY_USER_PROMPT = """Patient Health ID: {health_id}

Extract ONLY the following critical information:
1. Allergies (list all known allergies)
2. Current medications (name and dosage)
3. Chronic conditions (existing diagnoses)

Rules:
- Maximum 3 bullet points total
- No explanations or advice
- No assumptions
- Use format: "• Item: Details"

Medical Records:
{medical_records}"""
    
    SUMMARY_SYSTEM_PROMPT = """You are a medical document summarization assistant.
Extract key medical information from documents and create clear, structured summaries.
Always indicate confidence level and cite sources.
Do not add medical advice or diagnoses."""
    
    SUMMARY_USER_PROMPT = """Analyze this medical document and create TWO summaries:

1. PATIENT-FRIENDLY (simple language, 3-4 sentences)
2. DOCTOR-FRIENDLY (clinical detail, structured format)

Document text:
{document_text}

Also provide:
- Confidence level: Low/Medium/High
- Key findings (list format)
- Document type (e.g., Lab Report, Prescription, Scan Report)"""
    
    VOICE_TO_JSON_PROMPT = """Convert the following clinical voice transcript into a valid JSON object.

Required fields:
- diagnosis: string (primary diagnosis or reason for visit)
- medications: array of objects with 'name' and 'dose'
- tests_ordered: array of strings
- follow_up_days: integer (0 if not mentioned)
- urgency: "low" | "medium" | "high"
- notes: string (additional observations)

Rules:
- Return ONLY valid JSON
- No markdown formatting
- No explanations
- Use null if information not mentioned

Transcript:
{transcript}"""
    
    # Demo Credentials (for hackathon judges)
    DEMO_PATIENT = {
        'health_id': 'MV12345',
        'password': 'demo123',
        'name': 'Demo Patient'
    }
    
    DEMO_DOCTOR = {
        'username': 'dr_demo',
        'password': 'demo123',
        'name': 'Dr. Demo Physician'
    }
    
    DEMO_LAB = {
        'username': 'lab_demo',
        'password': 'demo123',
        'name': 'Demo Laboratory'
    }

# Development vs Production configuration
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # In production, ensure SECRET_KEY is set via environment variable

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}