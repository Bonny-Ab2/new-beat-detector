import madmom
#!/usr/bin/env python3
import os
import sys
import types
import tempfile
import numpy as np
import librosa
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_cors import CORS

# FIX: Mock madmom._internal before importing BeatNet
mock_internal = types.ModuleType('madmom._internal')
sys.modules['madmom._internal'] = mock_internal
sys.modules['madmom'] = types.ModuleType('madmom')

# Mock pyaudio
sys.modules['pyaudio'] = types.ModuleType('pyaudio')

# Now import models
from BeatNet.BeatNet import BeatNet
from beat_this.inference import File2Beats

app = Flask(__name__)
CORS(app)

beatnet = None
beatthis = None


def smart_bpm(beats):
    if len(beats) < 10:
        return 0, 0
    beats = np.array(beats)
    intervals = np.diff(beats)
    if len(intervals) == 0:
        return 0, 0
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


def detect_time_signature(beats, downbeat_indicators):
    downbeat_indices = np.where(downbeat_indicators == 1)[0]
    if len(downbeat_indices) < 3:
        return 4, 50
    beats_per_bar = np.diff(downbeat_indices)
    if len(beats_per_bar) == 0:
        return 4, 50
    counter = Counter(beats_per_bar)
    most_common = counter.most_common(1)[0][0]
    confidence = (counter[most_common] / len(beats_per_bar)) * 100
    if most_common in [2, 3, 4, 6]:
        return most_common, confidence
    return 4, confidence * 0.6


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models': {
            'beatnet': beatnet is not None,
            'beatthis': beatthis is not None
        }
    })


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
        audio, sr = librosa.load(temp_path, sr=22050, mono=True)
        duration = len(audio) / sr
        
        # Try BeatNet
        if beatnet is not None:
            print(f"🎯 BeatNet processing: {audio_file.filename}")
            try:
                results = beatnet.process(temp_path)
                beats = results[:, 0]
                downbeat_indicators = results[:, 1]
                
                if len(beats) > 0:
                    bpm_raw, conf = smart_bpm(beats)
                    bpm, correction = correct_bpm_octave(bpm_raw)
                    downbeat_indices = np.where(downbeat_indicators == 1)[0]
                    downbeats = beats[downbeat_indices].tolist()
                    ts, ts_conf = detect_time_signature(beats, downbeat_indicators)
                    
                    print(f"✅ BeatNet success: {len(beats)} beats, {len(downbeats)} downbeats")
                    return jsonify({
                        'success': True,
                        'source': 'beatnet',
                        'duration': round(duration, 2),
                        'bpm': round(bpm, 2),
                        'bpm_raw': round(bpm_raw, 2),
                        'bpm_confidence': round(conf, 2),
                        'bpm_correction': correction,
                        'time_signature': f"{ts}/4",
                        'time_signature_confidence': round(ts_conf, 2),
                        'beats': [round(float(b), 3) for b in beats],
                        'downbeats': [round(float(d), 3) for d in downbeats],
                        'beat_count': len(beats),
                        'downbeat_count': len(downbeats)
                    })
            except Exception as e:
                print(f"❌ BeatNet error: {e}")
        
        # Fallback to BeatThis
        if beatthis is not None:
            print(f"🔄 BeatThis fallback: {audio_file.filename}")
            try:
                beats, downbeats = beatthis(temp_path)
                
                if len(beats) > 0:
                    bpm_raw, conf = smart_bpm(beats)
                    bpm, correction = correct_bpm_octave(bpm_raw)
                    
                    indicators = np.zeros(len(beats))
                    for i, beat in enumerate(beats):
                        if any(abs(beat - db) < 0.01 for db in downbeats):
                            indicators[i] = 1
                    
                    ts, ts_conf = detect_time_signature(beats, indicators)
                    
                    return jsonify({
                        'success': True,
                        'source': 'beatthis',
                        'duration': round(duration, 2),
                        'bpm': round(bpm, 2),
                        'bpm_raw': round(bpm_raw, 2),
                        'bpm_confidence': round(conf, 2),
                        'bpm_correction': correction,
                        'time_signature': f"{ts}/4",
                        'time_signature_confidence': round(ts_conf, 2),
                        'beats': [round(float(b), 3) for b in beats],
                        'downbeats': [round(float(d), 3) for d in downbeats],
                        'beat_count': len(beats),
                        'downbeat_count': len(downbeats)
                    })
            except Exception as e:
                print(f"❌ BeatThis error: {e}")
                return jsonify({'error': f'BeatThis failed: {str(e)}'}), 500
        
        return jsonify({'error': 'No beats detected'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🎵 BEAT DETECTION SERVER")
    print("=" * 60)
    
    try:
        beatnet = BeatNet(1, mode='offline', inference_model='DBN', plot=False)
        print("✅ BeatNet loaded (primary)")
    except Exception as e:
        print(f"❌ BeatNet failed: {e}")
    
    try:
        beatthis = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
        print("✅ BeatThis loaded (fallback)")
    except Exception as e:
        print(f"❌ BeatThis failed: {e}")
    
    print("\n" + "=" * 60)
    print("🚀 Server running on http://0.0.0.0:5000")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
