let recognition = null;
let kayitYapiliyor = false;
let metin = '';

// Duygu analizi fonksiyonunu güncelle
async function duyguAnaliziYap(metin) {
    if (!metin || metin.trim().length < 2) return;
    
    try {
        const yanit = await fetch('/duygu-analizi', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({metin: metin})
        });

        const veri = await yanit.json();
        
        // Dinamik ilerleme çubukları oluştur
        let html = '<div class="duygu-sonuclar">';
        veri.forEach(duygu => {
            const renk = {
                'Pozitif': '#4CAF50',
                'Negatif': '#f44336', 
                'Nötr': '#2196F3'
            }[duygu.label];
            
            html += `
                <div class="duygu-bar">
                    <span>${duygu.label}</span>
                    <div class="ilerleme">
                        <div class="ilerleme-cubugu" 
                             style="width: ${duygu.oran}%; background: ${renk}">
                            %${duygu.oran.toFixed(1)}
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        document.getElementById('duyguSonucu').innerHTML = html;
    } catch (hata) {
        console.log('Analiz devam ediyor...');
    }
}

function konusmaTanimlamayiBaslat() {
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
        alert("Tarayıcınız konuşma tanıma özelliğini desteklemiyor.");
        return;
    }

    if (recognition) {
        recognition.stop();
        recognition = null;
    }

    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'tr-TR';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => mikrofonButonuGuncelle(true);
    recognition.onend = () => {
        mikrofonButonuGuncelle(false);
        kayitYapiliyor = false; // Kayıt durumu güncelleniyor
    };

    recognition.onresult = (event) => {
        metin = '';
        for (let i = 0; i < event.results.length; i++) {
            metin += event.results[i][0].transcript;
        }
        document.getElementById('yaziAlani').textContent = metin.trim();
        kelimeSayisiniGuncelle(metin);

        // Her seferinde metin güncellenirse duygu analizi yapalım
        duyguAnaliziYap(metin);
    };

    recognition.onerror = (event) => {
        console.error("Hata oluştu:", event.error);
        alert(`Hata: ${event.error}`);
        mikrofonButonuGuncelle(false);
        kayitYapiliyor = false; // Hata durumunda kayıt durumu sıfırlanıyor
    };
}

function kelimeSayisiniGuncelle(metin) {
    const kelimeSayisi = metin.trim().split(/\s+/).filter(Boolean).length;
    document.getElementById('kelimeSayisi').textContent = `Kelime sayısı: ${kelimeSayisi}`;
}

function mikrofonButonuGuncelle(kayitDurumu) {
    const buton = document.getElementById('mikrofonButonu');
    buton.textContent = kayitDurumu ? '⏹️ Kayıt Yapılıyor...' : '🎤 Mikrofonu Başlat';
    buton.classList.toggle('kayit', kayitDurumu);
}

document.getElementById('mikrofonButonu').addEventListener('click', () => {
    if (!kayitYapiliyor) {
        konusmaTanimlamayiBaslat();
        recognition.start();
        kayitYapiliyor = true;
    } else {
        recognition.stop();
    }
});
