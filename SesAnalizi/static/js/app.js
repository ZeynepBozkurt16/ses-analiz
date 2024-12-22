const socket = io();
let currentRecording = null;

function startRecording() {
    if (currentRecording) return;
    
    const filename = document.getElementById('filename').value;
    const button = document.getElementById('recordButton');
    const timer = document.getElementById('timer');
    
    button.disabled = true;
    button.textContent = 'Kayıt Yapılıyor...';
    let timeLeft = 10;
    
    axios.post('/start-recording')
        .then(() => {
            currentRecording = true;
            timer.textContent = `Kalan süre: ${timeLeft} saniye`;
            
            const countdown = setInterval(() => {
                timeLeft--;
                timer.textContent = `Kalan süre: ${timeLeft} saniye`;
                
                if (timeLeft <= 0) {
                    clearInterval(countdown);
                    finishRecording(filename);
                    button.textContent = 'Ses Kaydı Başlat';
                    button.disabled = false;
                    timer.textContent = '';
                    currentRecording = null;
                }
            }, 1000);
            
            setTimeout(() => {
                axios.post('/stop-recording');
            }, 10000);
        });
}

function finishRecording(filename) {
    axios.post('/record', { filename: filename })
        .then(response => {
            document.getElementById('waveform').src = 'data:image/png;base64,' + response.data.histogram;
            document.getElementById('spectrogram').src = 'data:image/png;base64,' + response.data.spectrogram;
            fetchRecordings();  // Added back to update the recordings list
        });
}

socket.on('analysis_update', (data) => {
    if (currentRecording) {
        document.getElementById('waveform').src = 'data:image/png;base64,' + data.histogram;
        document.getElementById('spectrogram').src = 'data:image/png;base64,' + data.spectrogram;
    }
});
function analyzeRecording(filename) {
    const button = document.querySelector(`button[onclick="analyzeRecording('${filename}')"]`);
    button.textContent = 'Analiz Ediliyor...';
    button.disabled = true;
    
    axios.post('/analyze', { filename: filename })
        .then(response => {
            document.getElementById('waveform').src = 'data:image/png;base64,' + response.data.histogram;
            document.getElementById('spectrogram').src = 'data:image/png;base64,' + response.data.spectrogram;
            button.textContent = 'Analiz Et';
            button.disabled = false;
        });
}

function deleteRecording(filename) {
    axios.post('/delete', { filename: filename })
        .then(() => fetchRecordings());
}

function fetchRecordings() {
    axios.get('/list')
        .then(response => {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            
            response.data.files.forEach(file => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span>${file}</span>
                    <div>
                        <button onclick="analyzeRecording('${file}')">Analiz Et</button>
                        <button onclick="deleteRecording('${file}')" style="background: #dc3545;">Sil</button>
                    </div>
                `;
                fileList.appendChild(li);
            });
        });
}

window.onload = fetchRecordings;
