from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route('/python', methods=['GET'])
def eval_python():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    try:
        result = eval(code)
        return jsonify({'result': str(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/java', methods=['GET'])
def eval_java():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.java') as f:
            f.write(code.encode())
            temp_path = f.name
        class_name = os.path.basename(temp_path).replace('.java', '')
        compile_process = subprocess.run(['javac', temp_path], capture_output=True, text=True)
        if compile_process.returncode != 0:
            return jsonify({'error': compile_process.stderr}), 500
        run_process = subprocess.run(['java', '-cp', os.path.dirname(temp_path), class_name], capture_output=True, text=True)
        os.unlink(temp_path)
        class_file = temp_path.replace('.java', '.class')
        if os.path.exists(class_file):
            os.unlink(class_file)
        if run_process.returncode != 0:
            return jsonify({'error': run_process.stderr}), 500
        return jsonify({'result': run_process.stdout})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)