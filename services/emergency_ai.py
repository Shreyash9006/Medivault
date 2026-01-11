import os
import sqlite3
from datetime import datetime

class EmergencyAI:
    """AI service for emergency critical summaries - Fast and Free"""
    
    def __init__(self, api_key=None, db_path='database/medivault.db'):
        """
        Initialize Emergency AI service
        
        Args:
            api_key (str): Hugging Face API key (optional)
            db_path (str): Path to SQLite database
        """
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
        self.db_path = db_path
    
    def get_emergency_summary(self, health_id):
        """
        Generate emergency summary for a patient
        MUST complete in <15 seconds
        
        Args:
            health_id (str): Patient's Health ID
            
        Returns:
            dict: Emergency summary
        """
        start_time = datetime.now()
        
        # Step 1: Retrieve existing emergency summary from database (FAST)
        cached_summary = self._get_cached_summary(health_id)
        
        if cached_summary:
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': True,
                'health_id': health_id,
                'emergency_summary': cached_summary['emergency_summary'],
                'last_updated': cached_summary['last_updated'],
                'confidence': cached_summary['confidence'],
                'source_count': cached_summary['source_count'],
                'response_time': response_time,
                'cached': True
            }
        
        # Step 2: If no cache, retrieve all medical records
        medical_records = self._get_patient_records(health_id)
        
        if not medical_records:
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'health_id': health_id,
                'emergency_summary': '• No medical records found\n• Patient data not available\n• Contact patient or family',
                'last_updated': datetime.now().isoformat(),
                'confidence': 'Low',
                'source_count': 0,
                'response_time': response_time,
                'cached': False
            }
        
        # Step 3: Generate emergency summary (rule-based, fast)
        summary = self._generate_emergency_summary_fast(medical_records)
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'health_id': health_id,
            'emergency_summary': summary['text'],
            'last_updated': datetime.now().isoformat(),
            'confidence': summary['confidence'],
            'source_count': len(medical_records),
            'response_time': response_time,
            'cached': False
        }
    
    def _get_cached_summary(self, health_id):
        """Retrieve cached emergency summary from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT emergency_summary, confidence, generated_at, COUNT(*)
                FROM ai_summaries
                WHERE health_id = ?
                GROUP BY health_id
                ORDER BY generated_at DESC
                LIMIT 1
            ''', (health_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'emergency_summary': result[0],
                    'confidence': result[1],
                    'last_updated': result[2],
                    'source_count': result[3]
                }
            
            return None
        
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def _get_patient_records(self, health_id):
        """Retrieve all medical records for a patient"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.doctor_summary, s.patient_summary, m.document_type
                FROM ai_summaries s
                JOIN medical_records m ON s.record_id = m.id
                WHERE s.health_id = ?
                ORDER BY m.upload_date DESC
            ''', (health_id,))
            
            records = cursor.fetchall()
            conn.close()
            
            medical_texts = []
            for record in records:
                doctor_summary, patient_summary, doc_type = record
                medical_texts.append(f"[{doc_type}]\n{doctor_summary}")
            
            return medical_texts
        
        except Exception as e:
            print(f"Record retrieval error: {e}")
            return []
    
    def _generate_emergency_summary_fast(self, medical_records):
        """
        Generate emergency summary using rule-based extraction (FAST)
        
        Args:
            medical_records (list): List of medical record texts
            
        Returns:
            dict: {'text': str, 'confidence': str}
        """
        combined_text = '\n\n'.join(medical_records).lower()
        
        emergency_info = []
        
        # Extract Allergies (CRITICAL)
        allergies = self._extract_allergies(combined_text)
        if allergies:
            emergency_info.append(f"• Allergies: {allergies}")
        else:
            emergency_info.append("• Allergies: Not documented")
        
        # Extract Medications (CRITICAL)
        medications = self._extract_medications(combined_text)
        if medications:
            emergency_info.append(f"• Current Medications: {medications}")
        else:
            emergency_info.append("• Current Medications: Not documented")
        
        # Extract Diagnoses (CRITICAL)
        diagnoses = self._extract_diagnoses(combined_text)
        if diagnoses:
            emergency_info.append(f"• Chronic Conditions: {diagnoses}")
        else:
            emergency_info.append("• Chronic Conditions: Not documented")
        
        summary_text = '\n'.join(emergency_info)
        
        # Determine confidence
        documented_count = sum(1 for info in emergency_info if "Not documented" not in info)
        if documented_count >= 2:
            confidence = 'High'
        elif documented_count == 1:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        return {
            'text': summary_text,
            'confidence': confidence
        }
    
    def _extract_allergies(self, text):
        """Extract allergy information"""
        allergy_keywords = ['allerg', 'reaction to', 'sensitive to']
        
        lines = text.split('\n')
        allergies = []
        
        for line in lines:
            if any(keyword in line for keyword in allergy_keywords):
                # Extract allergy names (common ones)
                common_allergens = ['penicillin', 'peanut', 'sulfa', 'latex', 
                                   'aspirin', 'iodine', 'egg', 'shellfish']
                
                for allergen in common_allergens:
                    if allergen in line:
                        allergies.append(allergen.title())
        
        return ', '.join(allergies) if allergies else None
    
    def _extract_medications(self, text):
        """Extract medication information"""
        med_keywords = ['medicat', 'prescri', 'taking', 'tablet', 'mg']
        
        lines = text.split('\n')
        medications = []
        
        for line in lines:
            if any(keyword in line for keyword in med_keywords):
                # Extract common medication names
                common_meds = ['metformin', 'insulin', 'aspirin', 'atorvastatin', 
                              'lisinopril', 'amlodipine', 'omeprazole']
                
                for med in common_meds:
                    if med in line:
                        # Try to extract dosage
                        dosage = self._extract_dosage(line)
                        if dosage:
                            medications.append(f"{med.title()} {dosage}")
                        else:
                            medications.append(med.title())
        
        return ', '.join(medications[:3]) if medications else None
    
    def _extract_dosage(self, text):
        """Extract dosage from text"""
        import re
        # Look for patterns like "500mg", "10 mg", etc.
        dosage_pattern = r'\d+\s*mg'
        match = re.search(dosage_pattern, text.lower())
        return match.group(0) if match else None
    
    def _extract_diagnoses(self, text):
        """Extract diagnosis information"""
        diag_keywords = ['diagnos', 'condition', 'disease']
        
        lines = text.split('\n')
        diagnoses = []
        
        for line in lines:
            if any(keyword in line for keyword in diag_keywords):
                # Extract common conditions
                common_conditions = ['diabetes', 'hypertension', 'asthma', 'copd',
                                    'heart disease', 'kidney disease', 'cancer']
                
                for condition in common_conditions:
                    if condition in line:
                        diagnoses.append(condition.title())
        
        return ', '.join(diagnoses[:3]) if diagnoses else None
    
    def log_emergency_access(self, health_id, accessed_by, ip_address='unknown'):
        """Log emergency mode access for audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO emergency_logs (health_id, accessed_by, ip_address)
                VALUES (?, ?, ?)
            ''', (health_id, accessed_by, ip_address))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"Emergency log error: {e}")
            return False
    
    def get_emergency_history(self, health_id):
        """Get emergency access history for a patient"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT accessed_by, access_time, ip_address
                FROM emergency_logs
                WHERE health_id = ?
                ORDER BY access_time DESC
                LIMIT 20
            ''', (health_id,))
            
            logs = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'accessed_by': log[0],
                    'access_time': log[1],
                    'ip_address': log[2]
                }
                for log in logs
            ]
        
        except Exception as e:
            print(f"Emergency history error: {e}")
            return []


# Convenience function
def get_emergency_info(health_id):
    """Quick function to get emergency summary"""
    emergency_service = EmergencyAI()
    return emergency_service.get_emergency_summary(health_id)


# Test function
if __name__ == '__main__':
    print("🧪 Testing Emergency AI Service...")
    
    emergency = EmergencyAI()
    
    test_health_id = 'MV12345'
    
    print(f"\n🚨 Getting emergency summary for: {test_health_id}")
    print("   Target response time: <15 seconds\n")
    
    result = emergency.get_emergency_summary(test_health_id)
    
    print("✅ EMERGENCY SUMMARY RESULT:")
    print(f"   Success: {result['success']}")
    print(f"   Response Time: {result['response_time']:.2f} seconds")
    print(f"   Cached: {result.get('cached', False)}")
    print(f"\n🚨 CRITICAL INFO:")
    print(result['emergency_summary'])
    print(f"\n📊 Confidence: {result['confidence']}")
    print(f"📄 Sources Used: {result['source_count']}")
    
    print("\n✅ Emergency AI test complete!")