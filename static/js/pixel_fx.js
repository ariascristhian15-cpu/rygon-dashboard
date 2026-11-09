/**
 * THIAN-CORE // PIXEL AUDIO & FX ENGINE
 * Sintetizador Web Audio API puro (8-bit arcade) sin archivos externos.
 */

class PixelFXEngine {
  constructor() {
    this.audioCtx = null;
    this.soundEnabled = localStorage.getItem("thian_sound_enabled") !== "false";
  }

  initContext() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === "suspended") {
      this.audioCtx.resume();
    }
  }

  toggleSound() {
    this.soundEnabled = !this.soundEnabled;
    localStorage.setItem("thian_sound_enabled", this.soundEnabled);
    if (this.soundEnabled) {
      this.initContext();
      this.playSuccessSound();
    }
    return this.soundEnabled;
  }

  playBlip() {
    if (!this.soundEnabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    try {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(440, this.audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, this.audioCtx.currentTime + 0.08);

      gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.08);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.08);
    } catch (e) {
      // Audio fallback silencioso
    }
  }

  playSuccessSound() {
    if (!this.soundEnabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    try {
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, i) => {
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime + i * 0.06);

        gain.gain.setValueAtTime(0.09, this.audioCtx.currentTime + i * 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + (i + 1) * 0.06);

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.start(this.audioCtx.currentTime + i * 0.06);
        osc.stop(this.audioCtx.currentTime + (i + 1) * 0.06);
      });
    } catch (e) {}
  }

  playKeyClick() {
    if (!this.soundEnabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    try {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.03, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.03);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.03);
    } catch (e) {}
  }
}

window.pixelFX = new PixelFXEngine();
