"""
MediVault AI Services Package

This package contains AI-powered services for medical document processing:
- ai_summarizer: GPT-4 medical document summarization
- emergency_ai: Emergency critical summary generation
- voice_service: Whisper voice-to-text transcription
- embeddings_service: Semantic search using embeddings
- health_score: Health scoring and risk assessment
"""

from .ai_summarizer import MedicalSummarizer
from .emergency_ai import EmergencyAI
from .voice_service import VoiceService
from .embeddings_service import EmbeddingsService

__all__ = [
    'MedicalSummarizer',
    'EmergencyAI',
    'VoiceService',
    'EmbeddingsService'
]

__version__ = '1.0.0'