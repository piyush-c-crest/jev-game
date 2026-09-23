/**
 * audio.js - Web Audio API Procedural Sound Synthesizer.
 * Creates retro 8-bit / arcade sound effects without external audio files.
 */

class SoundFX {
  constructor() {
    this.ctx = null;
    this.muted = localStorage.getItem('jev_game_muted') === 'true';
  }

  _initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  isMuted() {
    return this.muted;
  }

  toggleMute() {
    this.muted = !this.muted;
    localStorage.setItem('jev_game_muted', this.muted);
    return this.muted;
  }

  playTone(freq, type = 'sine', duration = 0.15, gainVal = 0.15, decay = true) {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

    gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
    if (decay) {
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    }

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  playAttack() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    // Pitch sweep slash
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sawtooth';

    const t = this.ctx.currentTime;
    osc.frequency.setValueAtTime(380, t);
    osc.frequency.exponentialRampToValueAtTime(70, t + 0.12);

    gain.gain.setValueAtTime(0.25, t);
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.12);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.12);
  }

  playCrit() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    // Impact + High Shimmer
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc1.type = 'square';
    osc1.frequency.setValueAtTime(520, t);
    osc1.frequency.exponentialRampToValueAtTime(90, t + 0.25);

    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(1200, t);
    osc2.frequency.exponentialRampToValueAtTime(2400, t + 0.2);

    gain.gain.setValueAtTime(0.3, t);
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.28);

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(this.ctx.destination);

    osc1.start(t);
    osc2.start(t);
    osc1.stop(t + 0.28);
    osc2.stop(t + 0.28);
  }

  playBlock() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(220, t);
    osc.frequency.exponentialRampToValueAtTime(140, t + 0.18);

    gain.gain.setValueAtTime(0.35, t);
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.18);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.18);
  }

  playPotion() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const notes = [440, 554.37, 659.25, 880];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 'sine', 0.14, 0.18);
      }, idx * 60);
    });
  }

  playGold() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const notes = [987.77, 1318.51, 1567.98];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 'triangle', 0.12, 0.2);
      }, idx * 50);
    });
  }

  playStep() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    this.playTone(110, 'sine', 0.08, 0.1);
  }

  playDefeat() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const notes = [293.66, 261.63, 220.00, 164.81];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 'sawtooth', 0.35, 0.2);
      }, idx * 140);
    });
  }

  playVictory() {
    if (this.muted) return;
    this._initContext();
    if (!this.ctx) return;

    const fanfare = [523.25, 659.25, 783.99, 1046.50];
    fanfare.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 'triangle', 0.28, 0.25);
      }, idx * 100);
    });
  }
}

// Global audio singleton
window.soundFX = new SoundFX();
