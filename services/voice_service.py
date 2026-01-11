from openai import OpenAI
import os
import json
from datetime import datetime

class VoiceService:
    """Voice-to-text and text-to-structured-data using Whisper + GPT-4"""
    
    def __init__(self, api_key=None):
        """
        Initialize Voice Service
        
        Args:
            api_key (str): OpenAI API key
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.whisper_model = 'whisper-1'
        self.gpt_model = 'gpt-4-turbo-preview'
    
    def transcribe_audio(self, audio_file_path, language=None):
        """
        Transcribe audio file to text using Whisper
        Supports: Hindi, Tamil, Telugu, English, and 90+ languages
        
        Args:
            audio_file_path (str): Path to audio file (mp3, wav, m4a, webm)
            language (str, optional): Language code (e.g., 'en', 'hi', 'ta', 'te')
            
        Returns:
            dict: {
                'success': bool,
                'transcript': str,
                'language': str,
                'duration': float,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'transcript': '',
            'language': language or 'auto-detect',
            'duration': 0,
            'error': None
        }
        
        try:
            # Open audio file
            with open(audio_file_path, 'rb') as audio_file:
                
                # Transcribe using Whisper
                if language:
                    # Specify language for better accuracy
                    transcription = self.client.audio.transcriptions.create(
                        model=self.whisper_model,
                        file=audio_file,
                        language=language,
                        response_format='verbose_json'
                    )
                else:
                    # Auto-detect language
                    transcription = self.client.audio.transcriptions.create(
                        model=self.whisper_model,
                        file=audio_file,
                        response_format='verbose_json'
                    )
                
                # Extract results
                result['success'] = True
                result['transcript'] = transcription.text
                result['language'] = transcription.language if hasattr(transcription, 'language') else 'unknown'
                result['duration'] = transcription.duration if hasattr(transcription, 'duration') else 0
        
        except Exception as e:
            result['error'] = str(e)
            print(f"Whisper transcription error: {e}")
        
        return result
    
    def transcript_to_structured_json(self, transcript, context='clinical_note'):
        """
        Convert voice transcript to structured JSON using GPT-4
        
        Args:
            transcript (str): Transcribed text from Whisper
            context (str): Type of note (clinical_note, prescription, lab_order)
            
        Returns:
            dict: Structured medical data
        """
        if context == 'clinical_note':
            return self._clinical_note_to_json(transcript)
        elif context == 'prescription':
            return self._prescription_to_json(transcript)
        else:
            return self._clinical_note_to_json(transcript)
    
    def _clinical_note_to_json(self, transcript):
        """
        Convert clinical note transcript to structured JSON
        
        Args:
            transcript (str): Clinical note transcript
            
        Returns:
            dict: Structured clinical data
        """
        prompt = f"""Convert the following clinical voice transcript into a valid JSON object.

Required fields:
- diagnosis: string (primary diagnosis or reason for visit)
- medications: array of objects with 'name', 'dose', 'frequency'
- tests_ordered: array of strings (lab tests or imaging ordered)
- follow_up_days: integer (days until follow-up, 0 if not mentioned)
- urgency: "low" | "medium" | "high"
- notes: string (additional observations or instructions)
- symptoms: array of strings (patient complaints)

STRICT RULES:
- Return ONLY valid JSON
- No markdown code blocks (no ```json)
- No explanations or preamble
- Use null if information not mentioned
- Use empty arrays [] for missing lists

Clinical Transcript:
{transcript}

JSON Output:"""

        try:
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical transcription assistant. Convert voice transcripts to structured JSON. Return ONLY valid JSON with no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistent structure
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up JSON (remove markdown if present)
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            structured_data = json.loads(result_text)
            
            # Ensure required fields exist
            structured_data.setdefault('diagnosis', None)
            structured_data.setdefault('medications', [])
            structured_data.setdefault('tests_ordered', [])
            structured_data.setdefault('follow_up_days', 0)
            structured_data.setdefault('urgency', 'medium')
            structured_data.setdefault('notes', '')
            structured_data.setdefault('symptoms', [])
            
            return {
                'success': True,
                'data': structured_data,
                'error': None
            }
        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {result_text}")
            return {
                'success': False,
                'data': None,
                'error': f'JSON parsing failed: {str(e)}'
            }
        
        except Exception as e:
            print(f"Structured JSON error: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def _prescription_to_json(self, transcript):
        """
        Convert prescription transcript to structured JSON
        
        Args:
            transcript (str): Prescription transcript
            
        Returns:
            dict: Structured prescription data
        """
        prompt = f"""Convert this prescription voice note to JSON.

Required fields:
- medications: array of objects with 'name', 'dose', 'frequency', 'duration_days'
- diagnosis: string
- instructions: string (special instructions for patient)
- follow_up_days: integer

Return ONLY valid JSON, no markdown.

Transcript:
{transcript}"""

        try:
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "Convert prescription transcripts to JSON. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON
            if '```' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            structured_data = json.loads(result_text)
            
            return {
                'success': True,
                'data': structured_data,
                'error': None
            }
        
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def process_voice_note(self, audio_file_path, language=None, context='clinical_note'):
        """
        Complete workflow: Audio → Transcript → Structured JSON
        
        Args:
            audio_file_path (str): Path to audio file
            language (str, optional): Language code
            context (str): Note type
            
        Returns:
            dict: Complete processing result
        """
        start_time = datetime.now()
        
        # Step 1: Transcribe audio
        transcription_result = self.transcribe_audio(audio_file_path, language)
        
        if not transcription_result['success']:
            return {
                'success': False,
                'transcript': None,
                'structured_data': None,
                'error': transcription_result['error'],
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
        
        # Step 2: Convert to structured JSON
        structured_result = self.transcript_to_structured_json(
            transcription_result['transcript'],
            context
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': structured_result['success'],
            'transcript': transcription_result['transcript'],
            'language': transcription_result['language'],
            'structured_data': structured_result['data'],
            'error': structured_result.get('error'),
            'processing_time': processing_time,
            'audio_duration': transcription_result['duration']
        }
    
    def get_supported_languages(self):
        """
        Get list of supported languages for Whisper
        
        Returns:
            list: Language codes and names
        """
        return [
            {'code': 'en', 'name': 'English'},
            {'code': 'hi', 'name': 'Hindi'},
            {'code': 'ta', 'name': 'Tamil'},
            {'code': 'te', 'name': 'Telugu'},
            {'code': 'mr', 'name': 'Marathi'},
            {'code': 'bn', 'name': 'Bengali'},
            {'code': 'gu', 'name': 'Gujarati'},
            {'code': 'kn', 'name': 'Kannada'},
            {'code': 'ml', 'name': 'Malayalam'},
            {'code': 'pa', 'name': 'Punjabi'},
            # Whisper supports 90+ languages total
        ]

# Convenience function
def transcribe_medical_voice(audio_file, language=None):
    """
    Quick function to process medical voice note
    
    Args:
        audio_file (str): Path to audio file
        language (str, optional): Language code
        
    Returns:
        dict: Transcription and structured data
    """
    service = VoiceService()
    return service.process_voice_note(audio_file, language)

# Test function
if __name__ == '__main__':
    print("🧪 Testing Voice Service...")
    
    service = VoiceService()
    
    # Check API key
    if not service.api_key:
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
    
    # Test transcript to JSON conversion (no audio needed)
    print("\n🗣️ Testing transcript to JSON conversion...")
    
    sample_transcript = """Patient came in complaining of fever and cough for three days. 
Temperature is 101 degrees Fahrenheit. Diagnosed with upper respiratory tract infection.
Prescribed Azithromycin 500 milligrams once daily for 5 days and Paracetamol 500 milligrams 
three times daily for fever. Also ordered complete blood count and chest x-ray.
Patient should follow up in one week. This is medium urgency."""
    
    print(f"\nSample Transcript:")
    print(f"   {sample_transcript[:100]}...\n")
    
    if service.api_key:
        print("🤖 Converting to structured JSON...\n")
        
        result = service.transcript_to_structured_json(sample_transcript, 'clinical_note')
        
        if result['success']:
            print("✅ STRUCTURED DATA:")
            print(json.dumps(result['data'], indent=2))
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("⏭️  Skipping API test (no API key)")
    
    # Display supported languages
    print("\n🌍 Supported Languages (Sample):")
    languages = service.get_supported_languages()
    for lang in languages[:5]:
        print(f"   {lang['code']}: {lang['name']}")
    
    print(f"\n   ... and {len(languages) - 5}+ more languages!")
    print("\n✅ Voice Service test complete!")