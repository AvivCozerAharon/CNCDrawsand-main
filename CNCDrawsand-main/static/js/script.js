const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const oneStrokeButton = document.getElementById('oneStroke');
const threeStrokesButton = document.getElementById('threeStrokes');
const clearCanvasButton = document.getElementById('clearCanvas');
const sendDrawingButton = document.getElementById('sendDrawing');
const modal = document.getElementById('modal');
const countryNameElement = document.getElementById('countryName');
const closeModalButton = document.getElementById('closeModal');
const loadingElement = document.getElementById('loading');

const timerElement = document.getElementById('timer');

ctx.imageSmoothingEnabled = true; 
ctx.imageSmoothingQuality = 'high'; 
let drawingHistory = [];  // Armazena o histórico de desenhos para desfazer
let isCtrlPressed = false;
let timer; 
let timeLeft = 5 * 60; 

let brushConfig = 1; 
let isDrawing = false;
let lastX = 0;
let lastY = 0;
let angle = 0;  
let drawingPositions = [];

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

function generateZenBackground() {
    let gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#f0e6d2'); 
    gradient.addColorStop(1, '#d1b89b'); 
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < canvas.width * canvas.height * 0.001; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const alpha = Math.random() * 0.4 + 0.2; 
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.fillRect(x, y, 2, 2); 
    }
}

function updateSelectedBrush() {
    oneStrokeButton.classList.toggle('active', brushConfig === 1);
    threeStrokesButton.classList.toggle('active', brushConfig === 3);
}

function startDrawing(event) {
    isDrawing = true;
    [lastX, lastY] = [event.offsetX, event.offsetY];
}

function draw(event) {
    if (!isDrawing) return;

    if (event.key === 'a') {
        angle -= 10;  
    } else if (event.key === 'd') {
        angle += 10;
    }

    const currentX = event.offsetX;
    const currentY = event.offsetY;

    const distance = Math.hypot(currentX - lastX, currentY - lastY);
    const steps = Math.ceil(distance / 5);

    for (let i = 0; i <= steps; i++) {
        const interpolatedX = lastX + (currentX - lastX) * (i / steps);
        const interpolatedY = lastY + (currentY - lastY) * (i / steps);

        drawingPositions.push({ x: interpolatedX, y: interpolatedY, size: brushConfig, angle: angle });

        // Salva cada posição no histórico de desenho
        drawingHistory.push({ action: 'draw', x: interpolatedX, y: interpolatedY });
        
        const offsets = getOffsets(brushConfig);
        offsets.forEach(({ offsetX, offsetY, color }) => {
            ctx.strokeStyle = color;
            ctx.lineWidth = 5;
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(lastX + offsetX, lastY + offsetY);
            ctx.lineTo(interpolatedX + offsetX, interpolatedY + offsetY);
            ctx.stroke();
        });
    }

    [lastX, lastY] = [currentX, currentY];
}
function undoDrawing() {
    if (drawingHistory.length === 0) return; // Não há nada para desfazer

    // Remove a última ação do histórico
    const lastAction = drawingHistory.pop();
    if (lastAction.action === 'draw') {
        // Redefine o canvas e redesenha as posições anteriores
        clearCanvas();
        drawingHistory.forEach(item => {
            if (item.action === 'draw') {
                ctx.beginPath();
                ctx.arc(item.x, item.y, brushConfig * 3, 0, 2 * Math.PI);
                ctx.fillStyle = 'rgba(110, 100, 70, 1)'; // Cor de preenchimento para desenho
                ctx.fill();
            }
        });
    }
}
document.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key === 'z') {
        undoDrawing();
    } else {
        changeBrushDirection(event);
    }
});


function getOffsets(config) {
    const lines = [];
    const offsetAngle = angle * (Math.PI / 180);

    if (config === 1) {
        const baseSpacing = 3; 
        const offsetX = baseSpacing * Math.cos(offsetAngle);
        const offsetY = baseSpacing * Math.sin(offsetAngle);

        if (Math.abs(offsetX) < 1e-6) {
            lines.push({ offsetX: 0, offsetY: -baseSpacing, color: 'rgba(194, 178, 128, 1)' });
            lines.push({ offsetX: 0, offsetY: baseSpacing, color: 'rgba(110, 100, 70, 1)' });
        } else if (Math.abs(offsetY) < 1e-6) {
            lines.push({ offsetX: -baseSpacing, offsetY: 0, color: 'rgba(194, 178, 128, 1)' });
            lines.push({ offsetX: baseSpacing, offsetY: 0, color: 'rgba(110, 100, 70, 1)' });
        } else { 
            lines.push({ offsetX: -offsetX, offsetY: -offsetY, color: 'rgba(194, 178, 128, 1)' });
            lines.push({ offsetX: offsetX, offsetY: offsetY, color: 'rgba(110, 100, 70, 1)' });
        }
    } else if (config === 3) {
        const baseSpacing = 6; 
        for (let i = -2; i <= 2; i++) {
            const offsetX = i * baseSpacing * Math.cos(offsetAngle);
            const offsetY = i * baseSpacing * Math.sin(offsetAngle);

            lines.push({
                offsetX,
                offsetY,
                color: i % 2 === 0 ? 'rgba(194, 178, 128, 1)' : 'rgba(110, 100, 70, 1)'
            });
        }
    }
    return lines;
}

function endDrawing() {
    isDrawing = false;
}

function clearCanvas() {
    generateZenBackground();
    drawingPositions = []; 
}

function changeBrushDirection(event) {
    if (event.key === 'a') {
        angle -= 10;  
    } else if (event.key === 'd') {
        angle += 10; 
    }
}

function getCountryFromLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            fetch(`http://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lon}&apiKey=79d860e0abf140faa4d925d4bb9e9cc6`)
            .then(response => response.json())
            .then(data => {
                const country = data.features && data.features[0] && data.features[0].properties.city || 'Desconhecido';
                countryNameElement.textContent = `Cidade: ${country}`;
                loadingElement.style.display = 'none';
            })
            .catch(() => {
                countryNameElement.textContent = 'Cidade: Desconhecido';
                loadingElement.style.display = 'none';
            });
        });
    } else {
        countryNameElement.textContent = 'Cidade: Desconhecido';
        loadingElement.style.display = 'none'; 
    }
}

closeModalButton.addEventListener('click', () => {
    modal.style.display = 'none';
});

canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', endDrawing);
canvas.addEventListener('mouseout', endDrawing);

oneStrokeButton.addEventListener('click', () => {
    brushConfig = 1;
    updateSelectedBrush();
});

threeStrokesButton.addEventListener('click', () => {
    brushConfig = 3;
    updateSelectedBrush();
});

clearCanvasButton.addEventListener('click', clearCanvas);

document.addEventListener('keydown', changeBrushDirection);


function startTimer() {
    if (timer) clearInterval(timer); // Limpa qualquer timer anterior
    timeLeft = 5 * 60; // Reinicia o tempo

    timer = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();

        if (timeLeft <= 0) {
            clearInterval(timer);
            sendDrawing();
        }
    }, 1000); // Atualiza a cada segundo
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

function stopTimer() {
    clearInterval(timer);
}

function sendDrawing() {
    if (!canvas) {
        alert("Canvas não encontrado!");
        return;
    }

    const drawingData = canvas.toDataURL("image/png");

    fetch("/submit", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ drawingData: drawingPositions })
    })
    .then(response => {
        if (response.ok) {
            // Se a resposta for bem-sucedida, redireciona para a página de confirmação
            window.location.href = "/camera";  // Redireciona para a página de "submit_page"
        } else {
            throw new Error("Erro ao enviar o desenho.");
        }
    })
    .catch(error => {
        console.error("Erro ao enviar o desenho:", error);
        alert("Erro ao enviar o desenho.");
    });
}



canvas.addEventListener('mousedown', () => {
    if (!timer) startTimer(); 
});

sendDrawingButton.addEventListener("click", () => {
    stopTimer(); 
    sendDrawing();
});


generateZenBackground();
timerElement.textContent = "5:00";
