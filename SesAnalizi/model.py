from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import librosa
import numpy as np

class AudioAnalyzer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        
    def analyze_audio(self, audio_path):
        # Ses özelliklerini çıkar
        features = self._extract_features(audio_path)
        
        # Yapay veri oluştur (gerçek uygulamada etiketli veriniz olmalı)
        X = np.array([features] * 10)  # 10 örnek oluştur
        y = np.array([0, 1] * 5)  # İki sınıflı etiketler
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
        
        # Modeli eğit
        self.model.fit(X_train, y_train)
        
        # Tahmin yap
        y_pred = self.model.predict(X_test)
        
        # Metrikleri hesapla
        acc = accuracy_score(y_test, y_pred)
        fm = f1_score(y_test, y_pred)
        
        return {
            'accuracy': float(acc),
            'f1_score': float(fm),
            'features': features.tolist()
        }
    
    def _extract_features(self, audio_path):
        # Ses dosyasını yükle
        y, sr = librosa.load(audio_path)
        
        # Temel özellikler
        mfcc = librosa.feature.mfcc(y=y, sr=sr).mean(axis=1)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr).mean()
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y).mean()
        
        return np.concatenate([mfcc, [spectral_centroid, spectral_rolloff, zero_crossing_rate]])
