from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import sys
import io
import urllib.parse

app = Flask(__name__)

class OutputCapture:
    def __init__(self):
        self.buffer = io.StringIO()
    def write(self, text):
        self.buffer.write(text)
    def get_value(self):
        return self.buffer.getvalue()

def has_java():
    try:
        subprocess.run(['javac', '-version'], capture_output=True, check=True)
        subprocess.run(['java', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

JAVA_AVAILABLE = has_java()

@app.route('/python', methods=['GET'])
def eval_python():
    code = urllib.parse.unquote_plus(request.args.get('code', ''))
    if not code:
        return jsonify({'error': 'No code provided', 'console': ''}), 400
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    output = OutputCapture()
    sys.stdout = output
    sys.stderr = output
    
    try:
        exec_result = eval(code)
        return jsonify({
            'result': str(exec_result) if exec_result is not None else 'undefined',
            'console': output.get_value()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'console': output.get_value()
        }), 500
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

@app.route('/java', methods=['GET'])
def eval_java():
    if not JAVA_AVAILABLE:
        return jsonify({
            'error': 'Java environment not available',
            'console': ''
        }), 500
        
    code = urllib.parse.unquote_plus(request.args.get('code', ''))
    if not code:
        return jsonify({'error': 'No code provided', 'console': ''}), 400
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.java') as f:
            f.write(code.encode())
            temp_path = f.name
        
        class_name = os.path.basename(temp_path).replace('.java', '')
        compile_result = subprocess.run(
            ['javac', temp_path],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return jsonify({
                'error': compile_result.stderr,
                'console': compile_result.stdout
            }), 500
        
        run_result = subprocess.run(
            ['java', '-cp', os.path.dirname(temp_path), class_name],
            capture_output=True,
            text=True
        )
        
        os.unlink(temp_path)
        class_file = temp_path.replace('.java', '.class')
        if os.path.exists(class_file):
            os.unlink(class_file)
        
        if run_result.returncode != 0:
            return jsonify({
                'error': run_result.stderr,
                'console': run_result.stdout
            }), 500
        
        return jsonify({
            'result': 'Program executed',
            'console': run_result.stdout
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'console': ''
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
