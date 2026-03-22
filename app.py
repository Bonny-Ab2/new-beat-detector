import os
import sys
import tempfile
import numpy as np
import librosa
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_cors import CORS
from beat_this.inference import File2Beats

app = Flask(__name__)
CORS(app)

print("Loading BeatThis...")
beatthis = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
print("BeatThis loaded")

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'message': 'Beat detection server is running'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': 'beatthis'})

@app.route('/detect', methods=['POST'])
def detect():
    print("Received request")
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name
    
    try:
        print(f"Processing: {audio_file.filename}")
        beats, downbeats = beatthis(temp_path)
        print(f"Got {len(beats)} beats")
        
        intervals = np.diff(beats)
        bpm = 60.0 / np.median(intervals) if len(intervals) > 0 else 0
        
        return jsonify({
            'success': True,
            'bpm': round(bpm, 2),
            'beats': beats.tolist(),
            'downbeats': downbeats.tolist()
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
