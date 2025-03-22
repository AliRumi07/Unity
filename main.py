from flask import Flask, jsonify
import subprocess
import sys
import os
import threading
import time

app = Flask(__name__)

def read_credentials(file_path):
    """Read credentials from file and return as list of tuples (username, key)"""
    credentials = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Process pairs of lines
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):  # Ensure we have both username and key
                username = lines[i].strip()
                key = lines[i + 1].strip()
                credentials.append((username, key))
    except Exception as e:
        print(f"Error reading credentials: {str(e)}")
        
    return credentials

def read_current_credentials(yaml_path):
    """Read current credentials from browserstack.yml"""
    current_username = None
    current_key = None
    
    try:
        with open(yaml_path, 'r') as f:
            for line in f:
                if 'userName:' in line:
                    current_username = line.split(':', 1)[1].strip()
                elif 'accessKey:' in line:
                    current_key = line.split(':', 1)[1].strip()
    except Exception as e:
        print(f"Error reading yaml: {str(e)}")
                
    return current_username, current_key

def update_yaml(yaml_path, username, access_key):
    """Update browserstack.yml with new credentials"""
    try:
        with open(yaml_path, 'r') as f:
            lines = f.readlines()
        
        with open(yaml_path, 'w') as f:
            for line in lines:
                if 'userName:' in line:
                    f.write(f'userName: {username}\n')
                elif 'accessKey:' in line:
                    f.write(f'accessKey: {access_key}\n')
                else:
                    f.write(line)
        return True
    except Exception as e:
        print(f"Error updating yaml: {str(e)}")
        return False

def get_next_credentials(all_creds, current_username, current_key):
    """Get next set of credentials after current ones"""
    if not current_username or not current_key:
        return all_creds[0]
        
    for i, (username, key) in enumerate(all_creds):
        if username == current_username and key == current_key:
            # Return next credentials or wrap around to first set
            if i + 1 < len(all_creds):
                return all_creds[i + 1]
            else:
                return all_creds[0]
                
    # If current credentials not found, start from beginning
    return all_creds[0]

def run_browserstack_sdk():
    """Run browserstack.py using browserstack-sdk"""
    try:
        # Check if browserstack.py exists
        if not os.path.exists('browserstack.py'):
            raise FileNotFoundError("browserstack.py not found")

        # Run browserstack.py using browserstack-sdk
        process = subprocess.Popen(['browserstack-sdk', 'python', 'browserstack.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        
        # Get output and errors
        stdout, stderr = process.communicate()
        
        result = {
            'output': stdout if stdout else '',
            'errors': stderr if stderr else '',
            'return_code': process.returncode
        }
        
        return result
        
    except Exception as e:
        return {
            'output': '',
            'errors': str(e),
            'return_code': -1
        }

@app.route('/rotate_and_run', methods=['GET'])
def rotate_and_run():
    """API endpoint to rotate credentials and run browserstack"""
    try:
        creds_file = 'user_key.txt'
        yaml_file = 'browserstack.yml'
        
        # Read all credentials
        all_credentials = read_credentials(creds_file)
        if not all_credentials:
            return jsonify({
                'status': 'error',
                'message': 'No credentials found in user_key.txt'
            }), 400
            
        # Read current credentials from yaml
        current_username, current_key = read_current_credentials(yaml_file)
        
        # Get next credentials
        next_username, next_key = get_next_credentials(all_credentials, current_username, current_key)
        
        # Update yaml file
        if not update_yaml(yaml_file, next_username, next_key):
            return jsonify({
                'status': 'error',
                'message': 'Failed to update credentials'
            }), 500
        
        # Run browserstack.py using browserstack-sdk
        result = run_browserstack_sdk()
        
        return jsonify({
            'status': 'success' if result['return_code'] == 0 else 'error',
            'credentials': {
                'previous': {'username': current_username, 'key': current_key},
                'current': {'username': next_username, 'key': next_key}
            },
            'browserstack_execution': {
                'output': result['output'],
                'errors': result['errors'],
                'return_code': result['return_code']
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

if __name__ == "__main__":
    print("Starting Flask server on http://0.0.0.0:8080")
    print("Available endpoints:")
    print("  - GET /health : Health check")
    print("  - GET /rotate_and_run : Rotate credentials and run browserstack")
    app.run(host='0.0.0.0', port=8080)
