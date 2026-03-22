import os
import sys
import tempfile
import numpy as np
import librosa
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import BeatThis
from beat_this.inference import File2Beats

app = Flask(__name__)
CORS(app)

print("Loading BeatThis...")
beatthis = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
print("BeatThis loaded")


def smart_bpm(beats):
    if len(beats) < 10:
        return 0, 0
    intervals = np.diff(beats)
    median_interval = np.median(intervals)
    bpm = 60.0 / median_interval
    std_interval = np.std(intervals)
    cv = std_interval / median_interval if median_interval > 0 else 1.0
    confidence = max(0, min(100, 100 - (cv * 100)))
    return bpm, confidence


def correct_bpm_octave(bpm):
    if bpm <= 0:
        return 0, "invalid"
    if 65 <= bpm <= 80:
        return bpm * 2, "half-time corrected"
    elif 140 <= bpm <= 180:
        return bpm / 2, "double-time corrected"
    return bpm, "no correction"


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model': 'beatthis'})


@app.route('/detect', methods=['POST'])
def detect():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name
    
    try:
        # Load audio to get duration
        audio, sr = librosa.load(temp_path, sr=22050, mono=True)
        duration = len(audio) / sr
        
        # Process with BeatThis
        beats, downbeats = beatthis(temp_path)
        
        if len(beats) == 0:
            return jsonify({'error': 'No beats detected'}), 500
        
        # Calculate BPM
        bpm_raw, conf = smart_bpm(beats)
        bpm, correction = correct_bpm_octave(bpm_raw)
        
        return jsonify({
            'success': True,
            'source': 'beatthis',
            'duration': round(duration, 2),
            'bpm': round(bpm, 2),
            'bpm_raw': round(bpm_raw, 2),
            'bpm_confidence': round(conf, 2),
            'bpm_correction': correction,
            'beats': [round(float(b), 3) for b in beats],
            'downbeats': [round(float(d), 3) for d in downbeats],
            'beat_count': len(beats),
            'downbeat_count': len(downbeats)
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
