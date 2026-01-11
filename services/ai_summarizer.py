import json
import os
from datetime import datetime
import re

class MedicalSummarizer:
    """AI-powered medical document summarization using rule-based extraction"""
    
    def __init__(self, api_key=None):
        """
        Initialize Medical Summarizer
        
        Args:
            api_key (str): API key (optional, not used in rule-based mode)
        """
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
    
    def generate_summaries(self, document_text, document_type='Medical Record'):
        """
        Generate three types of summaries from medical document
        
        Args:
            document_text (str): Extracted text from medical document
            document_type (str): Type of document
            
        Returns:
            dict: Summaries dictionary
        """
        if not document_text or len(document_text.strip()) < 20:
            return {
                'patient_summary': 'Document text is too short to summarize.',
                'doctor_summary': 'Insufficient data for clinical summary.',
                'emergency_summary': '• No critical information available',
                'confidence': 'Low',
                'key_findings': [],
                'document_type': document_type
            }
        
        try:
            # Rule-based extraction (works 100% offline!)
            patient_summary = self._create_patient_friendly_summary(document_text)
            doctor_summary = self._create_doctor_summary(document_text)
            emergency_summary = self._extract_emergency_info(document_text)
            key_findings = self._extract_key_findings(document_text)
            confidence = self._calculate_confidence(document_text)
            
            return {
                'patient_summary': patient_summary,
                'doctor_summary': doctor_summary,
                'emergency_summary': emergency_summary,
                'confidence': confidence,
                'key_findings': key_findings,
                'document_type': document_type
            }
            
        except Exception as e:
            print(f"Summarization error: {e}")
            return self._fallback_summary(document_text, document_type)
    
    def _create_patient_friendly_summary(self, text):
        """Create patient-friendly summary"""
        summary_parts = []
        text_lower = text.lower()
        
        # Extract diagnosis
        diagnosis = self._extract_diagnosis(text)
        if diagnosis:
            summary_parts.append(f"Diagnosis: {diagnosis}.")
        
        # Extract medications
        medications = self._extract_medications_simple(text)
        if medications:
            summary_parts.append(f"Medications prescribed: {', '.join(medications)}.")
        
        # Extract allergies
        allergies = self._extract_allergies(text)
        if allergies:
            summary_parts.append(f"⚠️ Allergies noted: {', '.join(allergies)}.")
        
        # Extract follow-up
        follow_up = self._extract_follow_up(text)
        if follow_up:
            summary_parts.append(f"Follow-up: {follow_up}.")
        
        if not summary_parts:
            # Extract first few sentences
            sentences = text.split('.')
            summary_parts = [s.strip() + '.' for s in sentences[:3] if len(s.strip()) > 20]
        
        return ' '.join(summary_parts[:5])
    
    def _create_doctor_summary(self, text):
        """Create clinical summary for doctors"""
        lines = text.split('\n')
        important_lines = []
        
        clinical_keywords = [
            'diagnosis', 'diagnos', 'prescription', 'prescribed',
            'medication', 'medicat', 'dosage', 'dose',
            'test', 'lab', 'result', 'blood', 'pressure',
            'temperature', 'hba1c', 'glucose', 'cholesterol'
        ]
        
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 10:
                continue
            
            line_lower = line_clean.lower()
            
            # Check if line contains clinical keywords
            if any(keyword in line_lower for keyword in clinical_keywords):
                important_lines.append(line_clean)
        
        if important_lines:
            return ' | '.join(important_lines[:8])
        
        # Fallback: return first 400 characters
        return text[:400].strip() + "..."
    
    def _extract_emergency_info(self, text):
        """Extract emergency critical information"""
        emergency_info = []
        
        # Extract allergies (CRITICAL)
        allergies = self._extract_allergies(text)
        if allergies:
            emergency_info.append(f"• Allergies: {', '.join(allergies)}")
        else:
            emergency_info.append("• Allergies: Not documented")
        
        # Extract current medications (CRITICAL)
        medications = self._extract_medications_detailed(text)
        if medications:
            meds_str = ', '.join([f"{m['name']} {m['dose']}" if m['dose'] else m['name'] for m in medications[:3]])
            emergency_info.append(f"• Current Medications: {meds_str}")
        else:
            emergency_info.append("• Current Medications: Not documented")
        
        # Extract chronic conditions (CRITICAL)
        diagnosis = self._extract_diagnosis(text)
        if diagnosis:
            emergency_info.append(f"• Chronic Conditions: {diagnosis}")
        else:
            emergency_info.append("• Chronic Conditions: Not documented")
        
        return '\n'.join(emergency_info[:3])
    
    def _extract_allergies(self, text):
        """Extract allergy information"""
        text_lower = text.lower()
        allergies = []
        
        # Common allergens
        common_allergens = [
            'penicillin', 'peanut', 'peanuts', 'sulfa', 'sulfonamide',
            'latex', 'aspirin', 'iodine', 'egg', 'eggs', 'shellfish',
            'tree nut', 'soy', 'wheat', 'milk', 'fish'
        ]
        
        for allergen in common_allergens:
            if allergen in text_lower:
                allergies.append(allergen.title())
        
        return list(set(allergies))  # Remove duplicates
    
    def _extract_medications_simple(self, text):
        """Extract medication names (simple)"""
        text_lower = text.lower()
        medications = []
        
        # Common medications
        common_meds = [
            'metformin', 'insulin', 'aspirin', 'atorvastatin',
            'lisinopril', 'amlodipine', 'omeprazole', 'levothyroxine',
            'albuterol', 'losartan', 'gabapentin', 'hydrochlorothiazide',
            'simvastatin', 'pravastatin', 'rosuvastatin',
            'azithromycin', 'amoxicillin', 'ciprofloxacin',
            'paracetamol', 'ibuprofen', 'acetaminophen'
        ]
        
        for med in common_meds:
            if med in text_lower:
                medications.append(med.title())
        
        return list(set(medications))[:5]
    
    def _extract_medications_detailed(self, text):
        """Extract medication with dosage"""
        medications = []
        lines = text.split('\n')
        
        # Pattern: medication name + dosage
        dosage_pattern = r'(\d+)\s*(mg|milligram|g|gram|ml|unit)'
        
        med_keywords = [
            'metformin', 'insulin', 'aspirin', 'atorvastatin',
            'paracetamol', 'ibuprofen', 'azithromycin'
        ]
        
        for line in lines:
            line_lower = line.lower()
            
            for med in med_keywords:
                if med in line_lower:
                    # Try to extract dosage
                    dosage_match = re.search(dosage_pattern, line_lower)
                    dose = dosage_match.group(0) if dosage_match else None
                    
                    medications.append({
                        'name': med.title(),
                        'dose': dose
                    })
        
        return medications[:5]
    
    def _extract_diagnosis(self, text):
        """Extract diagnosis information"""
        text_lower = text.lower()
        diagnoses = []
        
        # Common conditions
        common_conditions = [
            'type 2 diabetes', 'type 1 diabetes', 'diabetes mellitus', 'diabetes',
            'hypertension', 'high blood pressure',
            'asthma', 'copd', 'chronic obstructive',
            'heart disease', 'coronary artery',
            'kidney disease', 'renal failure',
            'upper respiratory tract infection', 'respiratory infection',
            'urinary tract infection', 'uti',
            'pneumonia', 'bronchitis',
            'gastritis', 'gerd',
            'hypothyroidism', 'hyperthyroidism'
        ]
        
        for condition in common_conditions:
            if condition in text_lower:
                diagnoses.append(condition.title())
                break  # Take first match
        
        return diagnoses[0] if diagnoses else None
    
    def _extract_follow_up(self, text):
        """Extract follow-up information"""
        text_lower = text.lower()
        
        # Look for follow-up patterns
        follow_up_patterns = [
            r'follow[- ]up in (\d+) (week|day|month)',
            r'(\d+) (week|day|month) follow[- ]up',
            r'return in (\d+) (week|day|month)',
            r'see you in (\d+) (week|day|month)'
        ]
        
        for pattern in follow_up_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return f"{match.group(1)} {match.group(2)}(s)"
        
        return None
    
    def _extract_key_findings(self, text):
        """Extract key findings as list"""
        findings = []
        text_lower = text.lower()
        
        finding_keywords = {
            'diagnosis': 'diagnos',
            'prescription': 'prescri',
            'allergy': 'allerg',
            'lab test': 'test ordered',
            'vital signs': 'blood pressure',
            'follow-up': 'follow-up'
        }
        
        for finding, keyword in finding_keywords.items():
            if keyword in text_lower:
                findings.append(finding.title())
        
        return findings[:5] or ['Medical document processed']
    
    def _calculate_confidence(self, text):
        """Calculate confidence based on document completeness"""
        text_lower = text.lower()
        
        # Check for key sections
        has_diagnosis = 'diagnos' in text_lower
        has_medication = 'medicat' in text_lower or 'prescri' in text_lower
        has_patient_info = 'patient' in text_lower or 'health id' in text_lower
        
        score = sum([has_diagnosis, has_medication, has_patient_info])
        
        if score >= 3:
            return 'High'
        elif score >= 2:
            return 'Medium'
        else:
            return 'Low'
    
    def _fallback_summary(self, document_text, document_type):
        """Fallback summary"""
        preview = document_text[:200].strip() + "..."
        
        return {
            'patient_summary': f'Medical document uploaded. Preview: {preview}',
            'doctor_summary': f'Document type: {document_type}. Full text available in records.',
            'emergency_summary': '• AI summary unavailable\n• Refer to original document',
            'confidence': 'Low',
            'key_findings': ['Document processed'],
            'document_type': document_type
        }
    
    def quick_summary(self, document_text, max_sentences=3):
        """Generate a quick summary"""
        sentences = document_text.split('.')
        summary_sentences = [s.strip() for s in sentences[:max_sentences] if len(s.strip()) > 20]
        return '. '.join(summary_sentences) + '.'


# Test function
if __name__ == '__main__':
    print("🧪 Testing Medical Summarizer (Rule-Based)...")
    
    sample_document = """MEDICAL PRESCRIPTION

Patient: Demo Patient
Health ID: MV12345

Diagnosis: Type 2 Diabetes Mellitus

Current Medications:
1. Metformin 500mg - twice daily with meals
2. Atorvastatin 10mg - at bedtime

Known Allergies: Penicillin, Peanuts

Follow-up in 2 weeks"""

    summarizer = MedicalSummarizer()
    result = summarizer.generate_summaries(sample_document, 'Prescription')
    
    print("\n✅ PATIENT SUMMARY:")
    print(f"   {result['patient_summary']}\n")
    
    print("✅ DOCTOR SUMMARY:")
    print(f"   {result['doctor_summary']}\n")
    
    print("✅ EMERGENCY SUMMARY:")
    print(f"   {result['emergency_summary']}\n")
    
    print(f"📊 Confidence: {result['confidence']}")
    print(f"🔍 Key Findings: {', '.join(result['key_findings'])}")
    
    print("\n✅ Test complete!")