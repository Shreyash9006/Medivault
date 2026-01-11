import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize SQLite database with schema and demo data"""
    
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect('database/medivault.db')
    cursor = conn.cursor()
    
    print("🔨 Creating database tables...")
    
    # Table 1: Users (Patients, Doctors, Labs)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT UNIQUE,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('patient', 'doctor', 'lab')),
        license_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 2: Medical Records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        document_type TEXT,
        file_path TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        uploaded_by TEXT,
        FOREIGN KEY (health_id) REFERENCES users(health_id)
    )
    ''')
    
    # Table 3: AI Summaries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        health_id TEXT NOT NULL,
        patient_summary TEXT,
        doctor_summary TEXT,
        emergency_summary TEXT,
        confidence TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES medical_records(id),
        FOREIGN KEY (health_id) REFERENCES users(health_id)
    )
    ''')
    
    # Table 4: Emergency Access Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergency_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        accessed_by TEXT NOT NULL,
        access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY (health_id) REFERENCES users(health_id)
    )
    ''')
    
    # Table 5: Voice Records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voice_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        doctor_id TEXT NOT NULL,
        transcript TEXT,
        structured_data TEXT,
        audio_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (health_id) REFERENCES users(health_id)
    )
    ''')
    
    # Table 6: Document Embeddings (for semantic search)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        health_id TEXT NOT NULL,
        embedding_vector TEXT,
        text_chunk TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES medical_records(id)
    )
    ''')
    
    print("✅ Database tables created successfully!")
    
    # Insert demo data
    print("📝 Inserting demo data...")
    
    # Hash demo password
    demo_password_hash = generate_password_hash('demo123')
    
    # Demo Patient
    cursor.execute('''
    INSERT OR IGNORE INTO users (health_id, name, phone, email, password, role)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ('MV12345', 'Demo Patient', '+919876543210', 'patient@demo.com', demo_password_hash, 'patient'))
    
    # Demo Doctor
    cursor.execute('''
    INSERT OR IGNORE INTO users (health_id, name, phone, email, password, role, license_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('MVDR001', 'Dr. Demo Physician', '+919123456789', 'doctor@demo.com', demo_password_hash, 'doctor', 'MCI12345'))
    
    # Demo Lab
    cursor.execute('''
    INSERT OR IGNORE INTO users (health_id, name, phone, email, password, role, license_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('MVLAB01', 'Demo Laboratory', '+919111111111', 'lab@demo.com', demo_password_hash, 'lab', 'LAB67890'))
    
    # Demo Medical Record for MV12345
    cursor.execute('''
    INSERT OR IGNORE INTO medical_records (id, health_id, document_type, file_path, uploaded_by)
    VALUES (?, ?, ?, ?, ?)
    ''', (1, 'MV12345', 'Prescription', 'static/uploads/demo_prescription.pdf', 'patient'))
    
    # Demo AI Summary for emergency mode
    cursor.execute('''
    INSERT OR IGNORE INTO ai_summaries (
        record_id, health_id, patient_summary, doctor_summary, emergency_summary, confidence
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        1,
        'MV12345',
        'Your recent checkup shows you have Type 2 Diabetes. You are taking Metformin twice daily. You have allergies to Penicillin and Peanuts. Follow up with your doctor in 2 weeks.',
        'Patient diagnosed with Type 2 Diabetes Mellitus. Currently on Metformin 500mg BD. HbA1c: 7.2%. Known allergies: Penicillin, Peanuts. Blood pressure stable. Recommend lifestyle modification and glucose monitoring.',
        '• Allergies: Penicillin, Peanuts\n• Current Medications: Metformin 500mg (2x daily)\n• Chronic Conditions: Type 2 Diabetes Mellitus',
        'High'
    ))
    
    # Additional demo medical record - Lab Report
    cursor.execute('''
    INSERT OR IGNORE INTO medical_records (id, health_id, document_type, file_path, uploaded_by)
    VALUES (?, ?, ?, ?, ?)
    ''', (2, 'MV12345', 'Lab Report', 'static/uploads/demo_lab_report.pdf', 'lab'))
    
    # Demo AI Summary for lab report
    cursor.execute('''
    INSERT OR IGNORE INTO ai_summaries (
        record_id, health_id, patient_summary, doctor_summary, emergency_summary, confidence
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        2,
        'MV12345',
        'Your blood sugar levels are slightly high. Your cholesterol is within normal range. Kidney function tests are normal.',
        'Fasting Blood Glucose: 145 mg/dL (elevated). HbA1c: 7.2%. Total Cholesterol: 180 mg/dL. HDL: 45 mg/dL. LDL: 110 mg/dL. Creatinine: 0.9 mg/dL (normal). eGFR: >60 (normal kidney function).',
        '• Blood Sugar: Elevated (145 mg/dL)\n• Cholesterol: Normal range\n• Kidney Function: Normal',
        'High'
    ))
    
    # Demo emergency access log
    cursor.execute('''
    INSERT OR IGNORE INTO emergency_logs (health_id, accessed_by, ip_address)
    VALUES (?, ?, ?)
    ''', ('MV12345', 'MVDR001', '192.168.1.1'))
    
    conn.commit()
    print("✅ Demo data inserted successfully!")
    
    # Display summary
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medical_records")
    record_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ai_summaries")
    summary_count = cursor.fetchone()[0]
    
    print(f"\n📊 Database Summary:")
    print(f"   Users: {user_count}")
    print(f"   Medical Records: {record_count}")
    print(f"   AI Summaries: {summary_count}")
    print(f"\n🎯 Demo Credentials:")
    print(f"   Patient Health ID: MV12345")
    print(f"   Doctor Username: MVDR001")
    print(f"   Lab Username: MVLAB01")
    print(f"   Password (all): demo123")
    print(f"\n🔒 Security: All passwords are now hashed with werkzeug.security")
    
    conn.close()
    print("\n✅ Database initialization complete!")

if __name__ == '__main__':
    init_database()