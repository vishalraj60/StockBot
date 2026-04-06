import os
from flask import Flask, request, jsonify, render_template
import markdown
from universal_analyzer import analyze_csv_file

app = Flask(__name__)
# Max upload size 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

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
            prediction_output = analyze_csv_file(filepath)
            
            # Format to beautiful HTML using markdown parser
            html_output = markdown.markdown(
                prediction_output, 
                extensions=['extra', 'nl2br', 'sane_lists']
            )
            
            return jsonify({'success': True, 'html': html_output})
            
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)
            return jsonify({'error': f'Failed to process file: {str(e)}\n\n{traceback_str}'}), 500
            
    return jsonify({'error': 'Allowed file type is .csv'}), 400

if __name__ == '__main__':
    print("🌐 Starting Universal CSV Web Server on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)
