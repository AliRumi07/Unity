from flask import Flask, jsonify
import os
import yaml
from threading import Lock
import subprocess
import logging

app = Flask(__name__)
lock = Lock()  # To handle concurrent requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('browserstack_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_credentials(file_path):
    credentials = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                username = lines[i].strip()
                access_key = lines[i + 1].strip()
                credentials.append((username, access_key))
    return credentials

def get_next_credentials(used_creds_file, all_credentials):
    try:
        with open(used_creds_file, 'r') as f:
            used_count = int(f.read().strip())
    except FileNotFoundError:
        used_count = 0
    
    if used_count >= len(all_credentials):
        raise Exception("All credentials have been used")
    
    with open(used_creds_file, 'w') as f:
        f.write(str(used_count + 1))
    
    return all_credentials[used_count]

def get_next_apk(used_apk_file):
    apk_files = ['app1.apk', 'app2.apk', 'app3.apk']
    try:
        with open(used_apk_file, 'r') as f:
            used_count = int(f.read().strip())
    except FileNotFoundError:
        used_count = 0
    
    if used_count >= len(apk_files):
        raise Exception("All APK files have been used")
    
    with open(used_apk_file, 'w') as f:
        f.write(str(used_count + 1))
    
    return apk_files[used_count]

def update_browserstack_yml(username, access_key, apk_file):
    config = {
        'userName': username,
        'accessKey': access_key,
        'app': f'./{apk_file}'
    }
    
    with open('browserstack.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def run_browserstack():
    try:
        logger.info("Starting browserstack.py execution")
        process = subprocess.Popen(['browserstack-sdk', 'browserstack.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info("browserstack.py executed successfully")
            return True, stdout.decode()
        else:
            logger.error(f"browserstack.py execution failed: {stderr.decode()}")
            return False, stderr.decode()
    except Exception as e:
        logger.error(f"Error running browserstack.py: {str(e)}")
        return False, str(e)

@app.route('/update_and_run', methods=['GET'])
def update_config_and_run():
    with lock:  # Ensure thread-safe operation
        try:
            CREDS_FILE = 'user_key.txt'
            USED_CREDS_COUNTER = 'used_credentials_counter.txt'
            USED_APK_COUNTER = 'used_apk_counter.txt'
            
            # Read all credentials
            all_credentials = read_credentials(CREDS_FILE)
            
            # Get next credentials and APK
            username, access_key = get_next_credentials(USED_CREDS_COUNTER, all_credentials)
            apk_file = get_next_apk(USED_APK_COUNTER)
            
            # Update browserstack.yml
            update_browserstack_yml(username, access_key, apk_file)
            
            # Run browserstack.py
            success, output = run_browserstack()
            
            return jsonify({
                'status': 'success' if success else 'error',
                'config_update': {
                    'username': username,
                    'access_key': access_key,
                    'apk_file': apk_file
                },
                'browserstack_execution': {
                    'success': success,
                    'output': output
                }
            })
            
        except Exception as e:
            logger.error(f"Error in update_and_run: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400

@app.route('/update', methods=['GET'])
def update_config():
    with lock:
        try:
            CREDS_FILE = 'user_key.txt'
            USED_CREDS_COUNTER = 'used_credentials_counter.txt'
            USED_APK_COUNTER = 'used_apk_counter.txt'
            
            all_credentials = read_credentials(CREDS_FILE)
            username, access_key = get_next_credentials(USED_CREDS_COUNTER, all_credentials)
            apk_file = get_next_apk(USED_APK_COUNTER)
            
            update_browserstack_yml(username, access_key, apk_file)
            
            return jsonify({
                'status': 'success',
                'username': username,
                'access_key': access_key,
                'apk_file': apk_file
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400

@app.route('/status', methods=['GET'])
def get_status():
    try:
        with open('browserstack.yml', 'r') as f:
            config = yaml.safe_load(f)
            return jsonify({
                'status': 'success',
                'current_config': config
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
