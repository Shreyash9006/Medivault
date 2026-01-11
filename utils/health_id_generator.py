import random
import string
import sqlite3
from datetime import datetime

class HealthIDGenerator:
    """Generate unique Health IDs for patients"""
    
    def __init__(self, prefix='MV', length=8):
        """
        Initialize Health ID generator
        
        Args:
            prefix (str): Prefix for Health ID (default: 'MV' for MediVault)
            length (int): Total length of Health ID including prefix
        """
        self.prefix = prefix
        self.length = length
        self.suffix_length = length - len(prefix)
    
    def generate(self):
        """
        Generate a unique Health ID
        
        Returns:
            str: Unique Health ID (e.g., 'MV12345')
        """
        # Generate random alphanumeric suffix (excluding confusing characters)
        # Exclude: 0, O, I, l to avoid confusion
        safe_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
        suffix = ''.join(random.choices(safe_chars, k=self.suffix_length))
        
        health_id = f"{self.prefix}{suffix}"
        return health_id
    
    def generate_unique(self, db_path='database/medivault.db'):
        """
        Generate a unique Health ID that doesn't exist in database
        
        Args:
            db_path (str): Path to SQLite database
            
        Returns:
            str: Unique Health ID
        """
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            health_id = self.generate()
            
            # Check if this ID already exists
            if not self._exists_in_db(health_id, db_path):
                return health_id
            
            attempts += 1
        
        # If we couldn't generate unique ID, add timestamp
        timestamp = datetime.now().strftime('%H%M%S')
        return f"{self.prefix}{timestamp[-self.suffix_length:]}"
    
    def _exists_in_db(self, health_id, db_path):
        """
        Check if Health ID already exists in database
        
        Args:
            health_id (str): Health ID to check
            db_path (str): Path to SQLite database
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE health_id = ?",
                (health_id,)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
        except Exception as e:
            print(f"Database check error: {e}")
            return False
    
    def validate(self, health_id):
        """
        Validate Health ID format
        
        Args:
            health_id (str): Health ID to validate
            
        Returns:
            bool: True if valid format, False otherwise
        """
        if not health_id:
            return False
        
        # Check length
        if len(health_id) != self.length:
            return False
        
        # Check prefix
        if not health_id.startswith(self.prefix):
            return False
        
        # Check suffix contains only alphanumeric characters
        suffix = health_id[len(self.prefix):]
        if not suffix.isalnum():
            return False
        
        return True

# Convenience function for quick generation
def generate_health_id():
    """
    Quick function to generate a unique Health ID
    
    Returns:
        str: Unique Health ID
    """
    generator = HealthIDGenerator()
    return generator.generate_unique()

# Test function
if __name__ == '__main__':
    print("🧪 Testing Health ID Generator...")
    
    generator = HealthIDGenerator()
    
    # Generate 5 sample IDs
    print("\n📋 Sample Health IDs:")
    for i in range(5):
        health_id = generator.generate()
        is_valid = generator.validate(health_id)
        print(f"   {i+1}. {health_id} - Valid: {is_valid}")
    
    # Test unique generation
    print("\n🔍 Testing unique generation with database:")
    unique_id = generator.generate_unique()
    print(f"   Generated: {unique_id}")
    
    # Test validation
    print("\n✅ Testing validation:")
    test_cases = [
        ('MV12345', True),
        ('MV1234', False),   # Too short
        ('AB12345', False),  # Wrong prefix
        ('MV1234X', True),
        ('', False),         # Empty
        ('MV@@###', False),  # Invalid characters
    ]
    
    for test_id, expected in test_cases:
        result = generator.validate(test_id)
        status = "✓" if result == expected else "✗"
        print(f"   {status} '{test_id}' -> {result} (expected: {expected})")