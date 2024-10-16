const video = document.querySelector('#video');
const canvas = document.querySelector('#canvas');
const snap = document.querySelector('#snap');
const fileInput = document.querySelector('#fileInput');
const context = canvas.getContext('2d');

// Accesso alla fotocamera
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Errore nell'accesso alla fotocamera:", err);
    });

// Scatta una foto quando viene premuto il pulsante
snap.addEventListener('click', () => {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/png');  // Ottieni l'immagine come stringa base64
    inviaImmagineAlServer(imageData);
});

// Gestisce il caricamento dell'immagine dal dispositivo
fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const imageData = e.target.result; // Dati dell'immagine in base64
            // Mostra l'immagine nel canvas
            const img = new Image();
            img.onload = function () {
                context.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = imageData;
            // Invia l'immagine al server
            inviaImmagineAlServer(imageData);
        };
        reader.readAsDataURL(file); // Legge il file come data URL (base64)
    }
});

// Funzione per inviare l'immagine al server
function inviaImmagineAlServer(imageData) {
    fetch('/upload', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            console.log('Testo riconosciuto:', data.text);
            document.getElementById('risultato').innerText = data.text;
        })
        .catch(error => {
            console.error('Errore:', error);
        });
}
// Function to send the image to the server
function inviaImmagineAlServer(imageData) {
fetch('/upload', {
method: 'POST',
body: JSON.stringify({ image: imageData }),
headers: { 'Content-Type': 'application/json' }
})
.then(response => response.json())
.then(data => {
    console.log('Feedback:', data.feedback);
    const risultato = document.getElementById('risultato');
    risultato.innerHTML = ''; // Clear previous content
    if (data.feedback && data.feedback.length > 0) {
        data.feedback.forEach(msg => {
            const p = document.createElement('p');
            p.innerText = msg;
            risultato.appendChild(p);
        });
    } else if (data.error) {
        risultato.innerText = `Error: ${data.error}`;
    } else {
        risultato.innerText = 'No feedback received.';
    }
})
.catch(error => {
    console.error('Errore:', error);
    document.getElementById('risultato').innerText = 'An error occurred while processing the image.';
});
}