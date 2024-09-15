from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/run-setup')
def run_setup():
    try:
        result = subprocess.run(['python', 'main.py', '--setup', 'mysetup'], capture_output=True, text=True)
        return f"Command executed successfully: {result.stdout}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
