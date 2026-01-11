import qrcode
import io
import base64
from PIL import Image

class QRGenerator:
    """Generate QR codes for Health IDs"""
    
    def __init__(self, base_url='http://localhost:5000/emergency'):
        """
        Initialize QR generator
        
        Args:
            base_url (str): Base URL for emergency mode access
        """
        self.base_url = base_url
    
    def generate_qr_code(self, health_id, save_path=None):
        """
        Generate QR code for a Health ID
        
        Args:
            health_id (str): Patient's Health ID
            save_path (str, optional): Path to save QR code image
            
        Returns:
            PIL.Image: QR code image object
        """
        # Create emergency access URL
        emergency_url = f"{self.base_url}?id={health_id}"
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Size of QR code (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,  # Size of each box in pixels
            border=4,  # Border size (minimum is 4)
        )
        
        # Add data to QR code
        qr.add_data(emergency_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save if path provided
        if save_path:
            img.save(save_path)
        
        return img
    
    def generate_qr_base64(self, health_id):
        """
        Generate QR code as base64 string (for HTML display)
        
        Args:
            health_id (str): Patient's Health ID
            
        Returns:
            str: Base64 encoded QR code image
        """
        # Generate QR code
        img = self.generate_qr_code(health_id)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_with_logo(self, health_id, logo_path=None, save_path=None):
        """
        Generate QR code with MediVault logo in center (optional)
        
        Args:
            health_id (str): Patient's Health ID
            logo_path (str, optional): Path to logo image
            save_path (str, optional): Path to save final image
            
        Returns:
            PIL.Image: QR code with logo
        """
        # Generate base QR code
        img = self.generate_qr_code(health_id)
        
        # Add logo if provided
        if logo_path:
            try:
                logo = Image.open(logo_path)
                
                # Calculate logo size (15% of QR code)
                qr_width, qr_height = img.size
                logo_size = int(qr_width * 0.15)
                
                # Resize logo
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Calculate position (center)
                logo_pos = (
                    (qr_width - logo_size) // 2,
                    (qr_height - logo_size) // 2
                )
                
                # Paste logo onto QR code
                img.paste(logo, logo_pos)
            except Exception as e:
                print(f"Warning: Could not add logo - {e}")
        
        # Save if path provided
        if save_path:
            img.save(save_path)
        
        return img
    
    def generate_for_patient(self, health_id, patient_name, save_dir='static/qrcodes'):
        """
        Generate QR code with patient info and save to file
        
        Args:
            health_id (str): Patient's Health ID
            patient_name (str): Patient's name
            save_dir (str): Directory to save QR code
            
        Returns:
            str: Path to saved QR code file
        """
        import os
        
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename
        filename = f"qr_{health_id}.png"
        save_path = os.path.join(save_dir, filename)
        
        # Generate and save QR code
        self.generate_qr_code(health_id, save_path)
        
        return save_path

# Convenience functions
def generate_health_id_qr(health_id, output_path=None):
    """
    Quick function to generate QR code for a Health ID
    
    Args:
        health_id (str): Health ID to encode
        output_path (str, optional): Where to save the QR code
        
    Returns:
        PIL.Image: QR code image
    """
    generator = QRGenerator()
    return generator.generate_qr_code(health_id, output_path)

def generate_qr_base64(health_id):
    """
    Quick function to generate base64 QR code
    
    Args:
        health_id (str): Health ID to encode
        
    Returns:
        str: Base64 encoded image string
    """
    generator = QRGenerator()
    return generator.generate_qr_base64(health_id)

# Test function
if __name__ == '__main__':
    print("🧪 Testing QR Code Generator...")
    
    # Test Health ID
    test_health_id = "MV12345"
    
    generator = QRGenerator()
    
    # Test 1: Generate basic QR code
    print(f"\n📱 Generating QR code for Health ID: {test_health_id}")
    qr_img = generator.generate_qr_code(test_health_id, 'test_qr.png')
    print(f"   ✓ QR code saved to: test_qr.png")
    print(f"   ✓ Emergency URL: http://localhost:5000/emergency?id={test_health_id}")
    
    # Test 2: Generate base64 version
    print(f"\n🔗 Generating base64 QR code...")
    base64_qr = generator.generate_qr_base64(test_health_id)
    print(f"   ✓ Base64 length: {len(base64_qr)} characters")
    print(f"   ✓ Prefix: {base64_qr[:50]}...")
    
    # Test 3: Generate for patient
    print(f"\n👤 Generating QR code for patient...")
    save_path = generator.generate_for_patient(test_health_id, "Demo Patient")
    print(f"   ✓ Saved to: {save_path}")
    
    print("\n✅ All tests passed!")