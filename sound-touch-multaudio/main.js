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
            pitch: pitchSlider.value,
            tempo: tempoSlider.value
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
            console.error(error);
        }
    }
}

function updateSeek(players, seekSlider) {
    if (players.length) {
        console.log("seeking");
        const totalDuration = players.reduce((acc, player) => acc + player.durationVal, 0);
        seekSlider.value = totalDuration / (players.length * 48000) / players[0].duration;
    }
}

playButton.addEventListener('click', () => {
    if (audioPlayers.length && !isPlaying) {
        audioPlayers.forEach(player => player.play());
        isPlaying = true;
        myInterval.push(setInterval(() => {
            updateSeek(audioPlayers, seekSlider);
        }, 1000));
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
        audioPlayers.forEach(player => {
            player.tempo = tempoSlider.value;
        });
    }
});

pitchSlider.addEventListener('input', () => {
    if (audioPlayers.length) {
        audioPlayers.forEach(player => {
            player.pitch = pitchSlider.value;
        });
    }
});

seekSlider.addEventListener('input', () => {
    let percentage = seekSlider.value * 100;
    if (audioPlayers.length) {
        audioPlayers.forEach(player => {
            player.seekPercent(percentage);
        });
    }
});

loadAudioPlayers(audioUrls);
