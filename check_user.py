# check_users.py
import sqlite3
from werkzeug.security import check_password_hash

conn = sqlite3.connect('database/medivault.db')
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT health_id, name, role, password FROM users")
users = cursor.fetchall()

print("=" * 60)
print("ALL USERS IN DATABASE:")
print("=" * 60)

for user in users:
    health_id, name, role, password_hash = user
    print(f"\nHealth ID: {health_id}")
    print(f"Name: {name}")
    print(f"Role: {role}")
    print(f"Password Hash: {password_hash[:50]}...")  # Show first 50 chars
    
    # Test if demo123 works
    if check_password_hash(password_hash, 'demo123'):
        print("✅ Password 'demo123' WORKS")
    else:
        print("❌ Password 'demo123' DOES NOT WORK")

conn.close()

print("\n" + "=" * 60)
print("EXPECTED DOCTOR CREDENTIALS:")
print("=" * 60)
print("Username (health_id): MVDR001 or dr_demo")
print("Password: demo123")