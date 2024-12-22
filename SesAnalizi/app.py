from flask import Flask, render_template, request, jsonify
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import librosa
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO
from flask_socketio import SocketIO
import queue
import uuid
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from multiprocessing import Process
from flask_cors import CORS
import requests
import torch.nn.functional as F





# Uygulama ve SocketIO ayarları
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app)

# Sabitler ve dizinler
SAMPLE_RATE = 44100
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

audio_queue = queue.Queue()
is_recording = False
stream = None



# Web soket bağlantısı
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('request_analysis')
def handle_analysis_request():
    if not audio_queue.empty():
        latest_audio = audio_queue.get()
        hist_image, spec_image = create_graphs(latest_audio)
        socketio.emit('analysis_update', {'histogram': hist_image, 'spectrogram': spec_image})

# Yardımcı fonksiyonlar
def generate_filename():
    return f"audio_{str(uuid.uuid4())[:8]}"

def create_graphs(audio):
    # Dalga formu grafiği oluştur
    plt.figure(figsize=(5, 3))
    plt.plot(audio, color='blue', alpha=0.7)
    plt.title("Ses Dalga Formu")
    plt.xlabel("Zaman")
    plt.ylabel("Genlik")
    plt.grid(True)
    waveform_buffer = BytesIO()
    plt.savefig(waveform_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    waveform_image = base64.b64encode(waveform_buffer.getvalue()).decode('utf-8')
    waveform_buffer.close()
    
    # Spektrogram grafiği oluştur
    plt.figure(figsize=(5, 3))
    plt.specgram(audio.flatten(), Fs=SAMPLE_RATE, NFFT=1024, noverlap=512, cmap="viridis")
    plt.title("Ses Verisi Spektrogramı")
    plt.xlabel("Zaman (saniye)")
    plt.ylabel("Frekans (Hz)")
    plt.colorbar(label="Yoğunluk")
    spec_buffer = BytesIO()
    plt.savefig(spec_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    spec_image = base64.b64encode(spec_buffer.getvalue()).decode('utf-8')
    spec_buffer.close()
    
    return waveform_image, spec_image

def audio_callback(indata, frames, time, status):
    global is_recording
    if is_recording:
        audio_queue.put(indata.copy())
        try:
            hist_image, spec_image = create_graphs(indata)
            socketio.emit('analysis_update', {'histogram': hist_image, 'spectrogram': spec_image})
        except Exception as e:
            print(f"Grafik hatası: {e}")

# Rotalar
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-recording', methods=['POST'])
def start_recording():
    global is_recording, stream
    is_recording = True
    stream = sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=2048, callback=audio_callback)
    stream.start()
    return jsonify({'success': True})

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    global is_recording, stream
    if stream:
        stream.stop()
        stream.close()
    is_recording = False
    return jsonify({'success': True})

@app.route('/record', methods=['POST'])
def record():
    filename = request.json.get('filename', generate_filename()) + '.wav'
    file_path = os.path.join(RECORDINGS_DIR, filename)
    
    audio_data = []
    while not audio_queue.empty():
        audio_data.append(audio_queue.get())
    
    if audio_data:
        audio_data = np.concatenate(audio_data)
        write(file_path, SAMPLE_RATE, audio_data)
        
        hist_image, spec_image = create_graphs(audio_data)
        
        files = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.wav')]
        
        return jsonify({
            'success': True,
            'histogram': hist_image,
            'spectrogram': spec_image,
            'files': files
        })
    
    return jsonify({'success': False})

@app.route('/list', methods=['GET'])
def list_recordings():
    files = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.wav')]
    return jsonify({'files': files})

@app.route('/analyze-live', methods=['POST'])
def analyze_live():
    if not audio_queue.empty():
        audio_data = audio_queue.get()
        hist_image, spec_image = create_graphs(audio_data)
        return jsonify({'histogram': hist_image, 'spectrogram': spec_image})
    return jsonify({'success': False})

@app.route('/delete', methods=['POST'])
def delete_recording():
    filename = request.json.get('filename')
    if filename:
        file_path = os.path.join(RECORDINGS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/analyze', methods=['POST'])
def analyze():
    filename = request.json.get('filename')
    file_path = os.path.join(RECORDINGS_DIR, filename)
    
    y, sr = librosa.load(file_path)
    hist_image, spec_image = create_graphs(y)
    
    return jsonify({'histogram': hist_image, 'spectrogram': spec_image})

@app.route('/konusma-yaziya')
def konusma_yaziya():
    return render_template('konusma_yaziya.html')

from transformers import pipeline
import torch

# Duygu analizi modelini başlangıçta bir kere yükle
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="savasy/bert-base-turkish-sentiment-cased",
    tokenizer="savasy/bert-base-turkish-sentiment-cased"
)

@app.route('/duygu-analizi', methods=['POST'])
def duygu_analizi():
    veri = request.get_json()
    metin = veri.get('metin', '')
    
    # Canlı duygu analizi yap
    sonuc = sentiment_analyzer(metin)[0]
    skor = sonuc['score'] * 100
    
    # Tüm duygu yüzdelerini hesapla
    if sonuc['label'] == 'POSITIVE':
        yanit = [
            {"label": "Pozitif", "oran": round(skor, 2)},
            {"label": "Nötr", "oran": round((100-skor)/2, 2)},
            {"label": "Negatif", "oran": round((100-skor)/2, 2)}
        ]
    else:
        yanit = [
            {"label": "Pozitif", "oran": round((100-skor)/2, 2)},
            {"label": "Nötr", "oran": round((100-skor)/2, 2)}, 
            {"label": "Negatif", "oran": round(skor, 2)}
        ]
    
    return jsonify(yanit)




# Uygulama başlatma
if __name__ == '__main__':
  
    socketio.run(app, debug=True,use_reloader=False)