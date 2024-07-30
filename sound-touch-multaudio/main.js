const BUFFER_SIZE = 1024;

class AudioPlayer {
    constructor({ emitter, pitch, tempo }) {
        this.emitter = emitter;
        this.context = new AudioContext();
        this.scriptProcessor = this.context.createScriptProcessor(BUFFER_SIZE, 2, 2);
        this.scriptProcessor.onaudioprocess = e => {
            const l = e.outputBuffer.getChannelData(0);
            const r = e.outputBuffer.getChannelData(1);
            const framesExtracted = this.simpleFilter.extract(this.samples, BUFFER_SIZE);
            if (framesExtracted === 0) {
                this.emitter.emit('stop');
            }
            for (let i = 0; i < framesExtracted; i++) {
                l[i] = this.samples[i * 2];
                r[i] = this.samples[i * 2 + 1];
            }
        };

        this.soundTouch = new SoundTouch();
        this.soundTouch.pitch = pitch;
        this.soundTouch.tempo = tempo;

        this.duration = undefined;
        this.volumeNode = this.context.createGain();
        this.volumeNode.gain.value = 0.5;
    }

    get pitch() {
        return this.soundTouch.pitch;
    }
    set pitch(pitch) {
        this.soundTouch.pitch = pitch;
    }

    get tempo() {
        return this.soundTouch.tempo;
    }
    set tempo(tempo) {
        this.soundTouch.tempo = tempo;
    }

    decodeAudioData(data) {
        return this.context.decodeAudioData(data);
    }

    setBuffer(buffer) {
        const bufferSource = this.context.createBufferSource();
        bufferSource.buffer = buffer;

        this.samples = new Float32Array(BUFFER_SIZE * 2);
        this.source = {
            extract: (target, numFrames, position) => {
                this.emitter.emit('state', { t: position / this.context.sampleRate });
                const l = buffer.getChannelData(0);
                const r = buffer.getChannelData(1);
                for (let i = 0; i < numFrames; i++) {
                    target[i * 2] = l[i + position];
                    target[i * 2 + 1] = r[i + position];
                }
                return Math.min(numFrames, l.length - position);
            },
        };
        this.simpleFilter = new SimpleFilter(this.source, this.soundTouch);

        this.duration = buffer.duration;
        this.emitter.emit('state', { duration: buffer.duration });
    }

    play() {
        this.scriptProcessor.connect(this.volumeNode);
        this.volumeNode.connect(this.context.destination);
    }

    pause() {
        this.scriptProcessor.disconnect(this.volumeNode);
        this.volumeNode.disconnect(this.context.destination);
    }

    get durationVal() {
        return this.simpleFilter.sourcePosition;
    }

    seekPercent(percent) {
        if (this.simpleFilter !== undefined) {
            this.simpleFilter.sourcePosition = Math.round(
                percent / 100 * this.duration * this.context.sampleRate
            );
        }
    }
}

const audioUrls = [
    './vocals.wav',
    './bass.wav',
    './drums.wav',
    './other.wav'
];

const playButton = document.getElementById('playButton');
const pauseButton = document.getElementById('pauseButton');
const tempoSlider = document.getElementById('tempoSlider');
const pitchSlider = document.getElementById('pitchSlider');
const seekSlider = document.getElementById('seekSlider');
const currentTimeDisplay = document.getElementById('currentTime');
const audioControlsContainer = document.getElementById('audioControls');
const mark = document.querySelector('.mark');
const multControler = document.querySelector('.multControler');

let audioPlayers = [];
let isPlaying = false;
let myInterval = [];

async function loadAudioPlayers(urls) {
    if (isPlaying) {
        audioPlayers.forEach(player => player.pause());
        isPlaying = false;
        clearInterval(myInterval[0]);
        myInterval = [];
    }

    audioPlayers.forEach(player => player.pause());
    audioPlayers = [];
    audioControlsContainer.innerHTML = ''; 

    for (const [index, url] of urls.entries()) {
        const audioPlayer = new AudioPlayer({
            emitter: {
                emit: () => {},
            },
            pitch: Math.pow(2, pitchSlider.value / 12),
            tempo: tempoSlider.value / 120
        });

        try {
            const response = await fetch(url);
            const buffer = await response.arrayBuffer();
            const audioData = await audioPlayer.decodeAudioData(buffer);
            audioPlayer.setBuffer(audioData);

            audioPlayers.push(audioPlayer);

            const volumeLabel = document.createElement('label');
            volumeLabel.setAttribute('for', `volumeSlider${index}`);
            volumeLabel.textContent = `Volume ${index + 1}:`;

            const volumeSlider = document.createElement('input');
            volumeSlider.type = 'range';
            volumeSlider.id = `volumeSlider${index}`;
            volumeSlider.min = '0';
            volumeSlider.max = '1';
            volumeSlider.step = '0.01';
            volumeSlider.value = '0.5';

            volumeSlider.addEventListener('input', (e) => {
                audioPlayer.volumeNode.gain.value = e.target.value;
            });

            const volumeDiv = document.createElement('div');
            volumeDiv.appendChild(volumeLabel);
            volumeDiv.appendChild(volumeSlider);
            audioControlsContainer.appendChild(volumeDiv);

        } catch (error) {
            console.error('Falha ao carregar o arquivo de áudio:', url, error);
        }
    }
}

function updateSeek(players, seekSlider) {
    if (players.length) {
        const totalDuration = players.reduce((acc, player) => acc + player.durationVal, 0);
        seekSlider.max = 100; // Ajusta o valor máximo para 100 para porcentagem
        seekSlider.value = (totalDuration / (players.length * 48000) / players[0].duration) * 100;
    }
}

function updateMarkPosition() {
    if (audioPlayers.length) {
        const percentage = seekSlider.value;
        const containerWidth = multControler.clientWidth;
        const markPosition = (percentage / 100) * containerWidth;
        mark.style.left = `${markPosition}px`;
    }
}

playButton.addEventListener('click', () => {
    if (audioPlayers.length && !isPlaying) {
        audioPlayers.forEach(player => player.play());
        isPlaying = true;
        myInterval.push(setInterval(() => {
            updateSeek(audioPlayers, seekSlider);
            updateMarkPosition();
        }, 100));
    }
});

pauseButton.addEventListener('click', () => {
    if (audioPlayers.length && isPlaying) {
        audioPlayers.forEach(player => player.pause());
        isPlaying = false;
        clearInterval(myInterval[0]);
        myInterval = [];
    }
});

tempoSlider.addEventListener('input', () => {
    if (audioPlayers.length) {
        const bpm = parseInt(tempoSlider.value, 10);
        const defaultBPM = 120;
        const tempoFactor = bpm / defaultBPM;
        audioPlayers.forEach(player => {
            player.tempo = tempoFactor;
        });
    }
});

pitchSlider.addEventListener('input', () => {
    if (audioPlayers.length) {
        const semitones = parseInt(pitchSlider.value, 10);
        const pitchFactor = Math.pow(2, semitones / 12);
        audioPlayers.forEach(player => {
            player.pitch = pitchFactor;
        });
    }
});

seekSlider.addEventListener('input', () => {
    let percentage = seekSlider.value;
    if (audioPlayers.length) {
        audioPlayers.forEach(player => {
            player.seekPercent(percentage);
        });
        updateMarkPosition();
    }
});

multControler.addEventListener('click', (e) => {
    const containerWidth = multControler.clientWidth;
    const offsetX = e.clientX - multControler.getBoundingClientRect().left;
    const percentage = Math.min(Math.max(0, (offsetX / containerWidth) * 100), 100);
    seekSlider.value = percentage;
    updateMarkPosition();

    if (audioPlayers.length) {
        audioPlayers.forEach(player => {
            player.seekPercent(percentage);
        });
    }
});

// Arrastar o "mark"
let isDragging = false;

mark.addEventListener('mousedown', (e) => {
    isDragging = true;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
});

function onMouseMove(e) {
    if (isDragging) {
        const containerRect = multControler.getBoundingClientRect();
        const markX = e.clientX - containerRect.left;
        const containerWidth = containerRect.width;
        const percentage = Math.min(Math.max(0, (markX / containerWidth) * 100), 100);
        seekSlider.value = percentage;
        updateMarkPosition();

        if (audioPlayers.length) {
            audioPlayers.forEach(player => {
                player.seekPercent(percentage);
            });
        }
    }
}

function onMouseUp() {
    isDragging = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
}

loadAudioPlayers(audioUrls);
