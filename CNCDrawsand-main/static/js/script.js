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

let brushConfig = 1; 
let isDrawing = false;
let lastX = 0;
let lastY = 0;
let angle = 0;  // Nova variável para controlar a direção do pincel
let drawingPositions = [];

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

function generateZenBackground() {
    // Criando um fundo mais fluido com gradiente e uma textura suave
    let gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#f0e6d2'); // Cor clara para o fundo (areia)
    gradient.addColorStop(1, '#d1b89b'); // Cor mais escura, para dar profundidade
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Adicionando a textura sutil de pedras ou areia
    for (let i = 0; i < canvas.width * canvas.height * 0.001; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const alpha = Math.random() * 0.4 + 0.2; // Transparência suave
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.fillRect(x, y, 2, 2); // Pequenos pontos, simulando textura
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

    const currentX = event.offsetX;
    const currentY = event.offsetY;

    drawingPositions.push({ x: currentX, y: currentY, size: brushConfig });

    const offsets = getOffsets(brushConfig);

    offsets.forEach(({ offset, color }) => {
        ctx.strokeStyle = color;
        ctx.lineWidth = 5;  // Aumentando a espessura para um efeito mais suave
        ctx.lineJoin = 'round'; // Aumenta a suavização nas bordas
        ctx.lineCap = 'round';  // Aumenta a suavização nas bordas
        ctx.beginPath();
        ctx.moveTo(lastX + offset, lastY + offset);
        ctx.lineTo(currentX + offset, currentY + offset);
        ctx.stroke();
    });

    [lastX, lastY] = [currentX, currentY];
}

function getOffsets(config) {
    const lines = [];

    if (config === 1) {
        const baseSpacing = 2.5; 
        lines.push({ offset: -baseSpacing, color: 'rgba(194, 178, 128, 1)' }); 
        lines.push({ offset: baseSpacing, color: 'rgba(110, 100, 70, 1)' }); 
    } else if (config === 3) {
        const baseSpacing = 5;
        for (let i = -2; i <= 2; i++) {
            lines.push({
                offset: i * baseSpacing,
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
        angle -= 10;  // Girar o pincel para a esquerda
    } else if (event.key === 'd') {
        angle += 10;  // Girar o pincel para a direita
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

function sendDrawing() {
    loadingElement.style.display = 'block'; 
    getCountryFromLocation();
    modal.style.display = 'flex'; 
    console.log(drawingPositions)
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
sendDrawingButton.addEventListener('click', sendDrawing);

document.addEventListener('keydown', changeBrushDirection);

generateZenBackground();
