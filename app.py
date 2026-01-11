from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
import json

# Import our services
from config import Config
from utils.health_id_generator import generate_health_id
from utils.qr_generator import generate_qr_base64
from utils.pdf_extractor import extract_text_from_file
from services.ai_summarizer import MedicalSummarizer
from services.emergency_ai import EmergencyAI
from services.voice_service import VoiceService
from services.embeddings_service import EmbeddingsService

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Session security settings
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# In production, enable: app.config['SESSION_COOKIE_SECURE'] = True

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/qrcodes', exist_ok=True)

# Initialize AI services with better error handling
summarizer = None
emergency_ai = None
voice_service = None
embeddings_service = None

try:
    from services.ai_summarizer import MedicalSummarizer
    from services.emergency_ai import EmergencyAI
    from services.voice_service import VoiceService
    from services.embeddings_service import EmbeddingsService
    
    summarizer = MedicalSummarizer()
    emergency_ai = EmergencyAI()
    voice_service = VoiceService()
    embeddings_service = EmbeddingsService()
    print("✅ AI services initialized successfully!")
except Exception as e:
    print(f"⚠️ AI services initialization failed: {e}")
    print("⚠️ Continuing with fallback mode...")

# ==================== HELPER FUNCTIONS ====================

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROUTES ====================
@app.route('/patient/summarize/<int:record_id>')
@login_required
def patient_summarize(record_id):
    """Generate AI summary for a specific record"""
    if session.get('user_role') != 'patient':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get the record
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM medical_records WHERE id = ?', (record_id,)).fetchone()
    
    if not record:
        flash('Record not found', 'error')
        return redirect(url_for('patient_dashboard'))
    
    # Extract text
    extracted_text = extract_text_from_file(record['file_path'])
    
    # Generate summaries
    summaries = summarizer.generate_summaries(extracted_text, record['document_type'])
    
    # Update database
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE ai_summaries 
        SET patient_summary = ?, doctor_summary = ?, emergency_summary = ?, confidence = ?
        WHERE record_id = ?
    ''', (
        summaries['patient_summary'],
        summaries['doctor_summary'],
        summaries['emergency_summary'],
        summaries['confidence'],
        record_id
    ))
    conn.commit()
    conn.close()
    
    flash('AI summary generated successfully!', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/')
def index():
    """Landing page with demo credentials"""
    return render_template('index.html', demo_credentials={
        'patient': app.config['DEMO_PATIENT'],
        'doctor': app.config['DEMO_DOCTOR'],
        'lab': app.config['DEMO_LAB']
    })


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    """Patient registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not name or not phone or not password:
            flash('Name, phone, and password are required', 'error')
            return redirect(url_for('patient_register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('patient_register'))
        
        # Generate unique Health ID
        health_id = generate_health_id()
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (health_id, name, phone, email, password, role)
                VALUES (?, ?, ?, ?, ?, 'patient')
            ''', (health_id, name, phone, email, password_hash))
            
            conn.commit()
            conn.close()
            
            # Auto-login after registration
            session['user_id'] = health_id
            session['user_name'] = name
            session['user_role'] = 'patient'
            
            flash(f'Registration successful! Your Health ID: {health_id}', 'success')
            return redirect(url_for('patient_dashboard'))
        
        except sqlite3.IntegrityError:
            flash('Phone number or email already registered', 'error')
            return redirect(url_for('patient_register'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('patient_register'))
    
    return render_template('patient_register.html')


@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    """Patient login"""
    if request.method == 'POST':
        health_id = request.form.get('health_id', '').strip().upper()
        password = request.form.get('password', '')
        
        if not health_id or not password:
            flash('Health ID and password are required', 'error')
            return redirect(url_for('patient_login'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE health_id = ? AND role = "patient"',
            (health_id,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['health_id']
            session['user_name'] = user['name']
            session['user_role'] = 'patient'
            flash('Login successful!', 'success')
            return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid Health ID or password', 'error')
    
    return render_template('patient_login.html')


@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    """Doctor login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('doctor_login'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE health_id = ? AND role = "doctor"',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['health_id']
            session['user_name'] = user['name']
            session['user_role'] = 'doctor'
            flash('Login successful!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('doctor_login.html')


@app.route('/lab/login', methods=['GET', 'POST'])
def lab_login():
    """Lab login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('lab_login'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE health_id = ? AND role = "lab"',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['health_id']
            session['user_name'] = user['name']
            session['user_role'] = 'lab'
            flash('Login successful!', 'success')
            return redirect(url_for('lab_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('lab_login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ==================== PATIENT ROUTES ====================

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard"""
    if session.get('user_role') != 'patient':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    health_id = session['user_id']
    
    # Get patient info
    conn = get_db_connection()
    
    # Get medical records
    records = conn.execute('''
        SELECT m.*, s.patient_summary, s.confidence
        FROM medical_records m
        LEFT JOIN ai_summaries s ON m.id = s.record_id
        WHERE m.health_id = ?
        ORDER BY m.upload_date DESC
    ''', (health_id,)).fetchall()
    
    # Get emergency access logs
    logs = conn.execute('''
        SELECT * FROM emergency_logs
        WHERE health_id = ?
        ORDER BY access_time DESC
        LIMIT 10
    ''', (health_id,)).fetchall()
    
    conn.close()
    
    # Generate QR code
    qr_code = generate_qr_base64(health_id)
    
    return render_template('patient_dashboard.html',
                         health_id=health_id,
                         qr_code=qr_code,
                         records=records,
                         logs=logs)


@app.route('/patient/upload', methods=['GET', 'POST'])
@login_required
def patient_upload():
    """Upload medical record"""
    if session.get('user_role') != 'patient':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Check if file is present
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        document_type = request.form.get('document_type', 'Medical Record')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        
        if file_length > app.config['MAX_CONTENT_LENGTH']:
            flash('File too large. Maximum size is 16MB', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Save file
                file.save(filepath)
                
                # Extract text from document
                extracted_text = extract_text_from_file(filepath)
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    flash('Could not extract text from document. Please ensure the file is readable.', 'error')
                    os.remove(filepath)  # Clean up
                    return redirect(request.url)
                
                # Generate AI summaries
                # Generate AI summaries
                if summarizer:
                    summaries = summarizer.generate_summaries(extracted_text, document_type)
                else:
                    # Fallback when AI service is not available
                    summaries = {
                        'patient_summary': 'Document uploaded successfully. AI processing unavailable - using basic extraction.',
                        'doctor_summary': extracted_text[:500] + '...',
                        'emergency_summary': '• Document uploaded\n• AI processing unavailable\n• Review original document',
                        'confidence': 'Low'
                    }
                
                # Save to database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Insert medical record
                cursor.execute('''
                    INSERT INTO medical_records (health_id, document_type, file_path, uploaded_by)
                    VALUES (?, ?, ?, 'patient')
                ''', (session['user_id'], document_type, filepath))
                
                record_id = cursor.lastrowid
                
                # Insert AI summary
                cursor.execute('''
                    INSERT INTO ai_summaries (
                        record_id, health_id, patient_summary, doctor_summary, 
                        emergency_summary, confidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    record_id,
                    session['user_id'],
                    summaries['patient_summary'],
                    summaries['doctor_summary'],
                    summaries['emergency_summary'],
                    summaries['confidence']
                ))
                
                conn.commit()
                conn.close()
                
                # Generate embedding for semantic search (run in background in production)
                try:
                    embeddings_service.store_document_embedding(
                        record_id,
                        session['user_id'],
                        extracted_text
                    )
                except Exception as e:
                    print(f"Embedding generation failed: {e}")
                    # Don't fail the upload if embedding fails
                
                flash('Document uploaded and processed successfully!', 'success')
                return redirect(url_for('patient_dashboard'))
            
            except Exception as e:
                flash(f'Document processing failed: {str(e)}', 'error')
                # Clean up file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
        else:
            flash('Invalid file type. Allowed: PDF, JPG, PNG', 'error')
    
    return render_template('upload.html')


# ==================== DOCTOR ROUTES ====================

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    """Doctor dashboard"""
    if session.get('user_role') != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('doctor_dashboard.html')


@app.route('/doctor/search', methods=['GET', 'POST'])
@login_required
def doctor_search():
    """Search patient by Health ID"""
    if session.get('user_role') != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        health_id = request.form.get('health_id', '').strip().upper()
        if health_id:
            return redirect(url_for('doctor_patient_view', health_id=health_id))
        else:
            flash('Please enter a Health ID', 'error')
    
    return render_template('doctor_search.html')


@app.route('/doctor/patient/<health_id>')
@login_required
def doctor_patient_view(health_id):
    """View patient medical history"""
    if session.get('user_role') != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get patient info
    patient = conn.execute(
        'SELECT * FROM users WHERE health_id = ? AND role = "patient"',
        (health_id,)
    ).fetchone()
    
    if not patient:
        conn.close()
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_search'))
    
    # Get medical records
    records = conn.execute('''
        SELECT m.*, s.doctor_summary, s.emergency_summary, s.confidence
        FROM medical_records m
        LEFT JOIN ai_summaries s ON m.id = s.record_id
        WHERE m.health_id = ?
        ORDER BY m.upload_date DESC
    ''', (health_id,)).fetchall()
    
    conn.close()
    
    return render_template('doctor_patient_view.html',
                         patient=patient,
                         records=records)


@app.route('/doctor/voice', methods=['GET', 'POST'])
@login_required
def doctor_voice():
    """Voice dictation page"""
    if session.get('user_role') != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('voice_dictation.html')


@app.route('/api/voice/transcribe', methods=['POST'])
@login_required
def api_voice_transcribe():
    """API endpoint for voice transcription"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'})
    
    audio_file = request.files['audio']
    filename = secure_filename(f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        audio_file.save(filepath)
        
        # Process voice note
        result = voice_service.process_voice_note(filepath)
        
        # Clean up audio file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== LAB ROUTES ====================

@app.route('/lab/dashboard')
@login_required
def lab_dashboard():
    """Lab dashboard"""
    if session.get('user_role') != 'lab':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get lab's upload history
    conn = get_db_connection()
    uploads = conn.execute('''
        SELECT m.*, u.name as patient_name
        FROM medical_records m
        JOIN users u ON m.health_id = u.health_id
        WHERE m.uploaded_by = 'lab'
        ORDER BY m.upload_date DESC
        LIMIT 20
    ''').fetchall()
    conn.close()
    
    return render_template('lab_dashboard.html', uploads=uploads)


@app.route('/lab/upload', methods=['GET', 'POST'])
@login_required
def lab_upload():
    """Lab upload report"""
    if session.get('user_role') != 'lab':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        health_id = request.form.get('health_id', '').strip().upper()
        file = request.files.get('file')
        
        if not health_id:
            flash('Health ID is required', 'error')
            return redirect(request.url)
        
        if not file or file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Verify patient exists
        conn = get_db_connection()
        patient = conn.execute(
            'SELECT * FROM users WHERE health_id = ? AND role = "patient"',
            (health_id,)
        ).fetchone()
        
        if not patient:
            conn.close()
            flash(f'Patient with Health ID {health_id} not found', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{health_id}_lab_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                
                # Extract and process
                extracted_text = extract_text_from_file(filepath)
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    flash('Could not extract text from document', 'error')
                    os.remove(filepath)
                    return redirect(request.url)
                
                summaries = summarizer.generate_summaries(extracted_text, 'Lab Report')
                
                # Save to database
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO medical_records (health_id, document_type, file_path, uploaded_by)
                    VALUES (?, 'Lab Report', ?, 'lab')
                ''', (health_id, filepath))
                
                record_id = cursor.lastrowid
                
                cursor.execute('''
                    INSERT INTO ai_summaries (
                        record_id, health_id, patient_summary, doctor_summary,
                        emergency_summary, confidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    record_id, health_id,
                    summaries['patient_summary'],
                    summaries['doctor_summary'],
                    summaries['emergency_summary'],
                    summaries['confidence']
                ))
                
                conn.commit()
                conn.close()
                
                flash(f'Lab report uploaded successfully for patient {health_id}!', 'success')
                return redirect(url_for('lab_dashboard'))
            
            except Exception as e:
                conn.close()
                flash(f'Upload failed: {str(e)}', 'error')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
        else:
            conn.close()
            flash('Invalid file type', 'error')
    
    return render_template('lab_upload.html')


# ==================== EMERGENCY MODE ====================

@app.route('/emergency', methods=['GET', 'POST'])
def emergency_mode():
    """Emergency mode - No login required"""
    if request.method == 'POST' or request.args.get('id'):
        health_id = request.form.get('health_id') or request.args.get('id')
        
        if not health_id:
            flash('Please enter a Health ID', 'error')
            return render_template('emergency.html')
        
        health_id = health_id.strip().upper()
        
        # Get emergency summary
        result = emergency_ai.get_emergency_summary(health_id)
        
        # Log emergency access
        emergency_ai.log_emergency_access(
            health_id,
            session.get('user_id', 'ANONYMOUS'),
            request.remote_addr
        )
        
        return render_template('emergency.html',
                             health_id=health_id,
                             summary=result)
    
    return render_template('emergency.html')


# ==================== API ENDPOINTS ====================

@app.route('/api/search', methods=['POST'])
@login_required
def api_semantic_search():
    """API endpoint for semantic search"""
    data = request.get_json()
    health_id = data.get('health_id')
    query = data.get('query')
    
    if not health_id or not query:
        return jsonify({'success': False, 'error': 'Missing parameters'})
    
    try:
        results = embeddings_service.search_with_context(health_id, query)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    # Handle favicon requests silently
    if request.path == '/favicon.ico':
        return '', 204
    
    # For other 404s, show a proper error page
    try:
        return render_template('index.html', demo_credentials={
            'patient': app.config['DEMO_PATIENT'],
            'doctor': app.config['DEMO_DOCTOR'],
            'lab': app.config['DEMO_LAB']
        }), 404
    except:
        return "<h1>404 - Page Not Found</h1><p>Go back to <a href='/'>Home</a></p>", 404
@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Server Error</h1><p>Something went wrong. Please try again.</p>", 500

@app.errorhandler(413)
def file_too_large(e):
    flash('File too large. Maximum size is 16MB', 'error')
    return redirect(request.referrer or url_for('index'))


# ==================== RUN APP ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)