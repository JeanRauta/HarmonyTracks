const BUFFER_SIZE = 1024;
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const masterVolumeNode = audioContext.createGain();
masterVolumeNode.gain.value = 1; // Define o volume master inicial para 100%

class AudioPlayer {
    constructor({ emitter, pitch, tempo }) {
        this.emitter = emitter;
        this.context = audioContext;
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
        this.volumeNode.gain.value = 1; // Define o volume inicial para 100%

        this.volumeNode.connect(masterVolumeNode); // Conecta o volume individual ao volume master
        masterVolumeNode.connect(this.context.destination); // Conecta o volume master ao destino do contexto de áudio

        this.isMuted = false;
        this.savedVolume = this.volumeNode.gain.value;
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
    }

    pause() {
        this.scriptProcessor.disconnect(this.volumeNode);
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

    mute() {
        if (!this.isMuted) {
            this.savedVolume = this.volumeNode.gain.value;
            this.volumeNode.gain.value = 0;
            this.isMuted = true;
        }
    }

    unmute() {
        if (this.isMuted) {
            this.volumeNode.gain.value = this.savedVolume;
            this.isMuted = false;
        }
    }
}

const audioUrls = [
    './vocals.wav',
    './bass.wav',
    './drums.wav',
    './other.wav'
];

const playPauseButton = document.getElementById('playPauseButton');
const tempoSlider = document.getElementById('tempoSlider');
const pitchSlider = document.getElementById('pitchSlider');
const seekSlider = document.getElementById('seekSlider');
const currentTimeDisplay = document.getElementById('currentTime');
const masterVolumeSlider = document.getElementById('masterVolumeSlider');
const masterVolumePercentage = document.getElementById('masterVolumePercentage');
const audioControlsContainer = document.getElementById('audioControls');
const mark = document.querySelector('.mark');
const multControler = document.querySelector('.multControler');
const loadingElement = document.getElementById('loading');
const contentElement = document.getElementById('content');

let audioPlayers = [];
let isPlaying = false;
let myInterval = [];

// Inicializa o seekSlider e mark
seekSlider.value = 0;
mark.style.left = '0px';

masterVolumeSlider.addEventListener('input', (e) => {
    masterVolumeNode.gain.value = e.target.value;
    masterVolumePercentage.textContent = `${Math.round(e.target.value * 100)}%`;
});

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

    const loadPromises = urls.map(async (url, index) => {
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
            volumeSlider.value = '1'; // Define o volume inicial para 100%

            const volumePercentage = document.createElement('span');
            volumePercentage.id = `volumePercentage${index}`;
            volumePercentage.textContent = '100%'; // Volume inicial em porcentagem

            volumeSlider.addEventListener('input', (e) => {
                const volume = e.target.value;
                volumePercentage.textContent = `${Math.round(volume * 100)}%`;
                audioPlayer.volumeNode.gain.value = volume;
            });

            const muteCheckbox = document.createElement('input');
            muteCheckbox.type = 'checkbox';
            muteCheckbox.id = `muteCheckbox${index}`;

            muteCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    audioPlayer.mute();
                    volumeSlider.disabled = true;
                } else {
                    audioPlayer.unmute();
                    volumeSlider.disabled = false;
                }
            });

            const volumeDiv = document.createElement('div');
            volumeDiv.appendChild(volumeLabel);
            volumeDiv.appendChild(volumeSlider);
            volumeDiv.appendChild(volumePercentage);
            volumeDiv.appendChild(muteCheckbox);
            audioControlsContainer.appendChild(volumeDiv);

        } catch (error) {
            console.error('Falha ao carregar o arquivo de áudio:', url, error);
        }
    });

    await Promise.all(loadPromises);

    // Oculta o elemento de carregamento e mostra o conteúdo
    loadingElement.style.display = 'none';
    contentElement.style.display = 'block';
}

function updateSeek(players, seekSlider) {
    if (players.length) {
        const totalDuration = players.reduce((acc, player) => acc + player.durationVal, 0);
        seekSlider.max = 100; // Ajusta o valor máximo para 100 para porcentagem
        seekSlider.value = (totalDuration / (players.length * 48000) / players[0].duration) * 100;
    }
}

function updateCurrentTime(players) {
    if (players.length) {
        const totalTime = players.reduce((acc, player) => acc + player.durationVal, 0);
        currentTimeDisplay.textContent = `${Math.floor(totalTime / 60)}:${Math.floor(totalTime % 60).toString().padStart(2, '0')}`;
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

playPauseButton.addEventListener('click', () => {
    if (audioPlayers.length) {
        if (isPlaying) {
            audioPlayers.forEach(player => player.pause());
            isPlaying = false;
            playPauseButton.textContent = 'Play';
            clearInterval(myInterval[0]);
            myInterval = [];
        } else {
            audioPlayers.forEach(player => player.play());
            isPlaying = true;
            playPauseButton.textContent = 'Pause';
            myInterval.push(setInterval(() => {
                updateSeek(audioPlayers, seekSlider);
                updateCurrentTime(audioPlayers); // Atualiza o tempo atual de reprodução
                updateMarkPosition();
            }, 100));
        }
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
