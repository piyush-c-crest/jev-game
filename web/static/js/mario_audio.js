/**
 * mario_audio.js - 100% Procedural NES Synthesizer for Super Mario Bros.
 * Uses the Web Audio API to reproduce authentic 8-bit 2A03 sound effects & overworld chiptune music.
 * Zero external audio files required.
 */

class MarioAudioEngine {
    constructor() {
        this.ctx = null;
        this.muted = false;
        this.bgmMuted = false;
        this.masterVolume = 0.3;
        this.bgmVolume = 0.18;
        this.isBgmPlaying = false;
        this.bgmTimer = null;
        this.noteIndex = 0;
        this.masterGain = null;
        this.bgmGain = null;
    }

    init() {
        if (!this.ctx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                this.ctx = new AudioContextClass();
                this.masterGain = this.ctx.createGain();
                this.masterGain.gain.setValueAtTime(this.masterVolume, this.ctx.currentTime);
                this.masterGain.connect(this.ctx.destination);

                this.bgmGain = this.ctx.createGain();
                this.bgmGain.gain.setValueAtTime(this.bgmVolume, this.ctx.currentTime);
                this.bgmGain.connect(this.masterGain);
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    setMuted(mute) {
        this.muted = mute;
        if (this.masterGain && this.ctx) {
            this.masterGain.gain.setValueAtTime(this.muted ? 0 : this.masterVolume, this.ctx.currentTime);
        }
    }

    toggleMute() {
        this.setMuted(!this.muted);
        return this.muted;
    }

    toggleBGM() {
        this.bgmMuted = !this.bgmMuted;
        if (this.bgmGain && this.ctx) {
            this.bgmGain.gain.setValueAtTime(this.bgmMuted ? 0 : this.bgmVolume, this.ctx.currentTime);
        }
        return !this.bgmMuted;
    }

    // Helper: create white/pink noise buffer for percussion & brick breaks
    createNoiseBuffer(duration = 0.2) {
        if (!this.ctx) return null;
        const bufferSize = this.ctx.sampleRate * duration;
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        return buffer;
    }

    // Jump sound (small or super)
    playJump(isSuper = false) {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';

        const now = this.ctx.currentTime;
        const startFreq = isSuper ? 130 : 175;
        const endFreq = isSuper ? 440 : 587;
        const duration = isSuper ? 0.22 : 0.18;

        osc.frequency.setValueAtTime(startFreq, now);
        osc.frequency.exponentialRampToValueAtTime(endFreq, now + duration);

        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + duration);

        osc.connect(gain);
        gain.connect(this.masterGain);

        osc.start(now);
        osc.stop(now + duration);
    }

    // Enemy Stomp (crunchy percussive pop)
    playStomp() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        // Pitch drop square wave
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.exponentialRampToValueAtTime(50, now + 0.12);

        gain.gain.setValueAtTime(0.3, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.12);

        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(now);
        osc.stop(now + 0.12);

        // Noise burst for crunchy NES stomp texture
        const noise = this.ctx.createBufferSource();
        noise.buffer = this.createNoiseBuffer(0.08);
        const noiseGain = this.ctx.createGain();
        noiseGain.gain.setValueAtTime(0.2, now);
        noiseGain.gain.linearRampToValueAtTime(0.01, now + 0.08);

        noise.connect(noiseGain);
        noiseGain.connect(this.masterGain);
        noise.start(now);
    }

    // Coin chime: iconic B5 -> E6
    playCoin() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';

        osc.frequency.setValueAtTime(987.77, now); // B5
        osc.frequency.setValueAtTime(1318.51, now + 0.08); // E6

        gain.gain.setValueAtTime(0.25, now);
        gain.gain.setValueAtTime(0.25, now + 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.42);

        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(now);
        osc.stop(now + 0.42);
    }

    // Power-up Mushroom appears
    playPowerupAppear() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const notes = [330, 392, 659, 523, 587, 784];
        const now = this.ctx.currentTime;
        const noteDuration = 0.06;

        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(freq, now + idx * noteDuration);

            gain.gain.setValueAtTime(0.18, now + idx * noteDuration);
            gain.gain.linearRampToValueAtTime(0.01, now + (idx + 1) * noteDuration);

            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now + idx * noteDuration);
            osc.stop(now + (idx + 1) * noteDuration);
        });
    }

    // Mario collects Power-up Mushroom (Rapid ascending 8-bit scale)
    playPowerup() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const notes = [293.66, 329.63, 370.0, 392.0, 440.0, 493.88, 554.37, 587.33, 659.25, 739.99, 783.99];
        const now = this.ctx.currentTime;
        const step = 0.045;

        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(freq, now + idx * step);

            gain.gain.setValueAtTime(0.22, now + idx * step);
            gain.gain.linearRampToValueAtTime(0.01, now + (idx + 1) * step);

            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now + idx * step);
            osc.stop(now + (idx + 1) * step);
        });
    }

    // Mario takes damage and shrinks to Small Mario
    playPowerdown() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const notes = [587.33, 523.25, 493.88, 440.0, 392.0, 329.63, 261.63];
        const step = 0.06;

        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(freq, now + idx * step);

            gain.gain.setValueAtTime(0.2, now + idx * step);
            gain.gain.linearRampToValueAtTime(0.01, now + (idx + 1) * step);

            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now + idx * step);
            osc.stop(now + (idx + 1) * step);
        });
    }

    // Brick bump (Small Mario hits solid brick)
    playBlockBump() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(110, now);
        osc.frequency.exponentialRampToValueAtTime(45, now + 0.15);

        gain.gain.setValueAtTime(0.3, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.15);

        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(now);
        osc.stop(now + 0.15);
    }

    // Brick smash (Super Mario shatters brick)
    playBrickBreak() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const noise = this.ctx.createBufferSource();
        noise.buffer = this.createNoiseBuffer(0.25);

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(400, now);
        filter.Q.setValueAtTime(1.5, now);

        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.35, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.25);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(this.masterGain);

        noise.start(now);
    }

    // Kick Koopa Shell
    playKickShell() {
        if (this.muted) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(90, now + 0.14);

        gain.gain.setValueAtTime(0.28, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.14);

        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(now);
        osc.stop(now + 0.14);
    }

    // Mario dies (Iconic descending sad death melody)
    playDie() {
        if (this.muted) return;
        this.stopBGM();
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        // B4, F5, F5, F5, E5, D5, C5
        const melody = [
            { f: 493.88, d: 0.12 },
            { f: 698.46, d: 0.12 },
            { f: 0, d: 0.04 },
            { f: 698.46, d: 0.12 },
            { f: 698.46, d: 0.12 },
            { f: 659.25, d: 0.12 },
            { f: 587.33, d: 0.12 },
            { f: 523.25, d: 0.28 },
        ];

        let offset = 0;
        melody.forEach(note => {
            if (note.f > 0) {
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'square';
                osc.frequency.setValueAtTime(note.f, now + offset);

                gain.gain.setValueAtTime(0.25, now + offset);
                gain.gain.linearRampToValueAtTime(0.01, now + offset + note.d);

                osc.connect(gain);
                gain.connect(this.masterGain);
                osc.start(now + offset);
                osc.stop(now + offset + note.d);
            }
            offset += note.d;
        });
    }

    // Stage Clear Fanfare
    playStageClear() {
        if (this.muted) return;
        this.stopBGM();
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const melody = [
            { f: 392, d: 0.12 }, // G4
            { f: 523, d: 0.12 }, // C5
            { f: 659, d: 0.12 }, // E5
            { f: 784, d: 0.12 }, // G5
            { f: 1046, d: 0.12 }, // C6
            { f: 1318, d: 0.25 }, // E6
            { f: 1046, d: 0.25 }, // C6
            { f: 415, d: 0.12 }, // Ab4
            { f: 523, d: 0.12 }, // C5
            { f: 622, d: 0.12 }, // Eb5
            { f: 830, d: 0.12 }, // Ab5
            { f: 1046, d: 0.12 }, // C6
            { f: 1244, d: 0.25 }, // Eb6
            { f: 1046, d: 0.25 }, // C6
            { f: 466, d: 0.12 }, // Bb4
            { f: 587, d: 0.12 }, // D5
            { f: 698, d: 0.12 }, // F5
            { f: 932, d: 0.12 }, // Bb5
            { f: 1174, d: 0.12 }, // D6
            { f: 1396, d: 0.25 }, // F6
            { f: 1174, d: 0.25 }, // D6
            { f: 1046, d: 0.5 }, // C6 long
        ];

        let offset = 0;
        melody.forEach(note => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(note.f, now + offset);

            gain.gain.setValueAtTime(0.25, now + offset);
            gain.gain.linearRampToValueAtTime(0.01, now + offset + note.d);

            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now + offset);
            osc.stop(now + offset + note.d);

            offset += note.d;
        });
    }

    // Classic 8-bit NES Overworld Theme Synthesizer Loop
    startBGM() {
        if (this.isBgmPlaying) return;
        this.init();
        if (!this.ctx) return;
        this.isBgmPlaying = true;

        // Note frequencies for the Overworld Theme
        const E7 = 2637, E6 = 1318.5, C6 = 1046.5, G6 = 1568, G5 = 784,
              A5 = 880, B5 = 987.8, Bb5 = 932.3, F6 = 1397, D6 = 1174.7;

        // Sequence of (frequency, duration in 16th notes, rest)
        const leadNotes = [
            // Intro
            [E6, 1], [E6, 1], [0, 1], [E6, 1], [0, 1], [C6, 1], [E6, 2],
            [G6, 2], [0, 2], [G5, 2], [0, 2],
            // Part A
            [C6, 2], [0, 1], [G5, 2], [0, 1], [E6, 2],
            [0, 1], [A5, 2], [B5, 2], [Bb5, 1], [A5, 2],
            [G5, 1.5], [E6, 1.5], [G6, 1.5], [A6 = 1760, 2], [F6, 1], [G6, 1],
            [0, 1], [E6, 2], [C6, 1], [D6, 1], [B5, 2],
        ];

        const sixteenthDuration = 0.11; // 136 BPM roughly
        let currentStep = 0;

        const scheduleNote = () => {
            if (!this.isBgmPlaying || !this.ctx) return;

            const [freq, beats] = leadNotes[currentStep];
            const dur = beats * sixteenthDuration;

            if (freq > 0 && !this.bgmMuted && !this.muted) {
                const now = this.ctx.currentTime;
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'square';
                osc.frequency.setValueAtTime(freq * 0.5, now); // Octave balanced

                gain.gain.setValueAtTime(0.12, now);
                gain.gain.linearRampToValueAtTime(0.01, now + dur * 0.85);

                osc.connect(gain);
                gain.connect(this.bgmGain);
                osc.start(now);
                osc.stop(now + dur * 0.9);
            }

            currentStep = (currentStep + 1) % leadNotes.length;
            this.bgmTimer = setTimeout(scheduleNote, dur * 1000);
        };

        scheduleNote();
    }

    stopBGM() {
        this.isBgmPlaying = false;
        if (this.bgmTimer) {
            clearTimeout(this.bgmTimer);
            this.bgmTimer = null;
        }
    }
}

// Global instance for game access
window.marioAudio = new MarioAudioEngine();
