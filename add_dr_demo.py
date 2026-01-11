import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('database/medivault.db')
cursor = conn.cursor()

# Generate password hash for 'demo123'
demo_password_hash = generate_password_hash('demo123')

# Add dr_demo user
try:
    cursor.execute('''
    INSERT INTO users (health_id, name, phone, email, password, role, license_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('dr_demo', 'Dr. Demo Physician', '+919123456789', 'doctor@demo.com', demo_password_hash, 'doctor', 'MCI12345'))
    
    conn.commit()
    print("✅ Successfully added dr_demo user!")
    print("\n" + "="*60)
    print("NEW LOGIN CREDENTIALS:")
    print("="*60)
    print("Username: dr_demo")
    print("Password: demo123")
    print("\n✅ You can now login with 'dr_demo' at /doctor/login")
    
except sqlite3.IntegrityError as e:
    print(f"❌ Error: {e}")
    print("The user 'dr_demo' might already exist")
    print("\nTrying to update existing user instead...")
    
    # Update existing dr_demo user
    cursor.execute('''
    UPDATE users 
    SET password = ?, name = ?, phone = ?, email = ?, license_number = ?
    WHERE health_id = 'dr_demo' AND role = 'doctor'
    ''', (demo_password_hash, 'Dr. Demo Physician', '+919123456789', 'doctor@demo.com', 'MCI12345'))
    
    conn.commit()
    print("✅ Updated dr_demo user successfully!")

# Verify the user was added
cursor.execute("SELECT health_id, name, role FROM users WHERE health_id = 'dr_demo'")
result = cursor.fetchone()

if result:
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    print(f"✅ User exists in database:")
    print(f"   Health ID: {result[0]}")
    print(f"   Name: {result[1]}")
    print(f"   Role: {result[2]}")
else:
    print("\n❌ User was not added to database")

conn.close()

print("\n" + "="*60)
print("ALL DOCTOR USERS IN DATABASE:")
print("="*60)

# Show all doctors
conn = sqlite3.connect('database/medivault.db')
cursor = conn.cursor()
cursor.execute("SELECT health_id, name FROM users WHERE role = 'doctor'")
doctors = cursor.fetchall()

for doc in doctors:
    print(f"  • Username: {doc[0]} | Name: {doc[1]}")

conn.close()