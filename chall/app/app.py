from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import bcrypt
import uuid
from datetime import datetime, timedelta
from admin_bot import visit_url
import threading
import time
import os


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY','random')

users = {}
pastes = {}

def get_current_time():
    date_header = request.headers.get('Date')
    if date_header:
        try:
            return datetime.strptime(date_header, '%a, %d %b %Y %H:%M:%S %Z')
        except:
            pass
    return datetime.now()

admin_id = str(uuid.uuid4())
users['admin'] = {'user_id': admin_id,'password': os.getenv('ADMIN_PASSWORD','pass')}

# Flag is in the paste_id
flag_paste_id = "FLAG{REDACTED}"
pastes[flag_paste_id] = {'paste_id': flag_paste_id,'title': 'Flag Paste','content': 'This is for some other day!','language': 'text','expiration_time': (datetime.now() - timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT'),'user_id': admin_id,'is_expired': True}


def process_report(paste_url):
    """Process the report in the background"""
    time.sleep(5)
    visit_url(paste_url)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_time = get_current_time()
    for paste in pastes.values():
        expiration_time = datetime.strptime(paste['expiration_time'], '%a, %d %b %Y %H:%M:%S GMT')
        paste['is_expired'] = current_time > expiration_time
    
    user_pastes = [paste for paste in pastes.values() if paste['user_id'] == session['user_id']]
    return render_template('home.html', pastes=user_pastes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and password == users[username]['password']:
            session['username'] = username
            session['user_id'] = users[username]['user_id']
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user_id = str(uuid.uuid4())
        users[username] = {
            'user_id': user_id,
            'password': password
        }
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/create_paste', methods=['POST'])
def create_paste():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    language = request.form.get('language')
    expiration = request.form.get('expiration')
    
    if not all([title, content, language, expiration]):
        flash('All fields are required')
        return redirect(url_for('index'))
    
    paste_id = str(uuid.uuid4())
    expiration_time = get_current_time() + timedelta(hours=int(expiration))
    
    pastes[paste_id] = {
        'paste_id': paste_id,
        'title': title,
        'content': content,
        'language': language,
        'expiration_time': expiration_time.strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'user_id': session['user_id'],
        'is_expired': False
    }
    
    return redirect(url_for('view_paste', paste_id=paste_id))

@app.route('/paste/<paste_id>')
def view_paste(paste_id):
    if paste_id not in pastes:
        return 'Paste not found', 404

    paste = pastes[paste_id]
    is_admin_paste = paste['user_id'] == users['admin']['user_id']
    
    if is_admin_paste and ('username' not in session or session['username'] != 'admin'):
        return 'You are not authorized to view this paste', 403

    expiration_time = datetime.strptime(paste['expiration_time'], '%a, %d %b %Y %H:%M:%S GMT')
    if get_current_time() > expiration_time:
        paste['is_expired'] = True
        return 'Paste has expired', 403


    paste_username = ''
    for username, user_data in users.items():
        if user_data['user_id'] == paste['user_id']:
            paste_username = username
            break
    
    paste = {
        'paste_id': paste['paste_id'],
        'title': paste['title'],
        'content': paste['content'],
        'language': paste['language'],
        'expiration_time': paste['expiration_time'],
        'user_id': paste['user_id'],
        'username': paste_username,
        'is_expired': paste.get('is_expired', False)
    }
    
    return render_template('view_paste.html', paste=paste)


@app.route('/report/<paste_id>')
def report_paste(paste_id):
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    if paste_id not in pastes:
        return jsonify({'status': 'error', 'message': 'Paste not found'}), 404
    
    paste = pastes[paste_id]
    expiration_time = datetime.strptime(paste['expiration_time'], '%a, %d %b %Y %H:%M:%S GMT')
    current_time = get_current_time()
    
    if current_time > expiration_time:
        paste['is_expired'] = True
        return jsonify({'status': 'error', 'message': 'Paste has expired'}), 403
    
    paste_url = url_for('view_paste', paste_id=paste_id, _external=True)
    thread = threading.Thread(target=process_report, args=(paste_url,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Paste reported successfully','paste_id': paste_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
