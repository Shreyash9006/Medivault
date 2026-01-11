from openai import OpenAI
import os
import json
from datetime import datetime

class HealthScoreService:
    """AI-powered health scoring and risk assessment using GPT-4"""
    
    def __init__(self, api_key=None):
        """
        Initialize Health Score Service
        
        Args:
            api_key (str): OpenAI API key
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.model = 'gpt-4-turbo-preview'
    
    def calculate_health_score(self, patient_data):
        """
        Calculate comprehensive health score (1-10)
        
        Args:
            patient_data (dict): {
                'medications': list,
                'diagnoses': list,
                'lab_results': list,
                'vital_signs': dict,
                'age': int,
                'lifestyle': dict (optional)
            }
            
        Returns:
            dict: {
                'score': float (1-10),
                'category': str,
                'risk_factors': list,
                'recommendations': list,
                'confidence': str
            }
        """
        try:
            # Prepare prompt for GPT-4
            prompt = f"""Analyze this patient's health data and provide a comprehensive health score.

Patient Data:
{json.dumps(patient_data, indent=2)}

Provide a health score from 1-10 where:
- 9-10: Excellent health
- 7-8: Good health
- 5-6: Fair health, some concerns
- 3-4: Poor health, needs attention
- 1-2: Critical health issues

Return ONLY a valid JSON object:
{{
  "score": float (1-10),
  "category": "Excellent/Good/Fair/Poor/Critical",
  "risk_factors": ["factor1", "factor2", ...],
  "recommendations": ["action1", "action2", ...],
  "areas_of_concern": ["concern1", "concern2", ...],
  "positive_indicators": ["indicator1", "indicator2", ...],
  "confidence": "Low/Medium/High"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical health assessment AI. Provide objective health scores based on patient data. Do not diagnose or prescribe."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            
            # Ensure required fields
            result.setdefault('score', 5.0)
            result.setdefault('category', 'Fair')
            result.setdefault('risk_factors', [])
            result.setdefault('recommendations', [])
            result.setdefault('confidence', 'Medium')
            
            return result
            
        except Exception as e:
            print(f"Health score calculation error: {e}")
            return {
                'score': 5.0,
                'category': 'Unable to assess',
                'risk_factors': ['Insufficient data'],
                'recommendations': ['Consult with healthcare provider'],
                'confidence': 'Low'
            }
    
    def get_personalized_insights(self, health_id, medical_records):
        """
        Generate personalized health insights
        
        Args:
            health_id (str): Patient's Health ID
            medical_records (list): List of medical record summaries
            
        Returns:
            dict: Personalized insights and recommendations
        """
        try:
            combined_records = '\n\n'.join(medical_records[:10])
            
            prompt = f"""Based on this patient's medical history, provide personalized health insights.

Medical History:
{combined_records}

Provide actionable insights in JSON format:
{{
  "key_trends": ["trend1", "trend2", ...],
  "preventive_actions": ["action1", "action2", ...],
  "warning_signs": ["sign1", "sign2", ...],
  "lifestyle_suggestions": ["suggestion1", "suggestion2", ...],
  "follow_up_priority": "Low/Medium/High"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Provide evidence-based health insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if '```' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            print(f"Insights generation error: {e}")
            return {
                'key_trends': [],
                'preventive_actions': [],
                'warning_signs': [],
                'lifestyle_suggestions': [],
                'follow_up_priority': 'Medium'
            }

# Test function
if __name__ == '__main__':
    print("🧪 Testing Health Score Service...")
    
    service = HealthScoreService()
    
    # Sample patient data
    sample_data = {
        'medications': [
            {'name': 'Metformin', 'dose': '500mg', 'frequency': 'twice daily'}
        ],
        'diagnoses': ['Type 2 Diabetes Mellitus'],
        'lab_results': [
            {'test': 'HbA1c', 'value': '7.2', 'unit': '%'},
            {'test': 'Fasting Glucose', 'value': '145', 'unit': 'mg/dL'}
        ],
        'vital_signs': {
            'blood_pressure': '130/85',
            'heart_rate': '72',
            'bmi': '28.5'
        },
        'age': 45
    }
    
    if service.api_key:
        print("\n📊 Calculating health score...")
        result = service.calculate_health_score(sample_data)
        
        print(f"\n✅ Health Score: {result['score']}/10")
        print(f"   Category: {result['category']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"\n   Risk Factors: {', '.join(result['risk_factors'][:3])}")
        print(f"   Recommendations: {', '.join(result['recommendations'][:3])}")
    else:
        print("⚠️  OPENAI_API_KEY not set")
    
    print("\n✅ Health Score Service test complete!")