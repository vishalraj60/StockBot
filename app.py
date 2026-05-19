import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import markdown
from universal_analyzer import analyze_csv_file, ask_advisor
from database import init_db, save_analysis, get_all_history, get_settings, update_settings

app = Flask(__name__)
app.secret_key = 'super_secret_stockbot_key'
# Max upload size 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Init database
init_db()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    settings = get_settings()
    return render_template('index.html', username=settings.get('username', 'Vishal Raj'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        settings = get_settings()
        if password == settings.get('password', 'admin'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid Password')
    return render_template('login.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file segment provided!'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
        
    if file and file.filename.endswith('.csv'):
        # Keep temp space clean
        temp_dir = '/tmp/csv_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        filepath = os.path.join(temp_dir, file.filename)
        
        try:
            file.save(filepath)
            
            # Predict using our CrewAI script
            prediction_output, chart_data = analyze_csv_file(filepath)
            
            # Format to beautiful HTML using markdown parser
            html_output = markdown.markdown(
                prediction_output, 
                extensions=['extra', 'nl2br', 'sane_lists']
            )
            
            # Save the result to history
            save_analysis(file.filename, html_output)
            
            return jsonify({'success': True, 'html': html_output, 'chart_data': chart_data})
            
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)
            return jsonify({'error': f'Failed to process file: {str(e)}\n\n{traceback_str}'}), 500
            
    return jsonify({'error': 'Allowed file type is .csv'}), 400

@app.route('/api/history', methods=['GET'])
def history():
    return jsonify({'success': True, 'history': get_all_history()})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    if request.method == 'POST':
        data = request.json
        api_key = data.get('groq_api_key', '')
        # Allow passing empty or updated keys
        temperature = float(data.get('temperature', 0.2))
        username = data.get('username', 'Vishal Raj')
        password = data.get('password', 'admin')
        update_settings(api_key, temperature, username, password)
        return jsonify({'success': True, 'message': 'Settings updated'})
    else:
        return jsonify({'success': True, 'settings': get_settings()})

@app.route('/api/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    message = data.get('message', '')
    context_data = data.get('context', [])
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    try:
        response = ask_advisor(message, context_data)
        
        # Format response to HTML using markdown parser
        html_output = markdown.markdown(
            response, 
            extensions=['extra', 'nl2br', 'sane_lists']
        )
        return jsonify({'success': True, 'response': html_output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print(f"🌐 Starting Universal CSV Web Server on port {port}...")
    app.run(host='0.0.0.0', port=port)
