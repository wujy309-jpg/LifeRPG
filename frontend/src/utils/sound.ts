// 音效管理器
class SoundManager {
  private static instance: SoundManager;
  private audioContext: AudioContext | null = null;
  private enabled: boolean = true;

  private constructor() {
    this.enabled = localStorage.getItem('liferpg_sound') !== 'disabled';
  }

  static getInstance(): SoundManager {
    if (!SoundManager.instance) {
      SoundManager.instance = new SoundManager();
    }
    return SoundManager.instance;
  }

  private getAudioContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    return this.audioContext;
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
    localStorage.setItem('liferpg_sound', enabled ? 'enabled' : 'disabled');
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  // 播放音符
  private playTone(frequency: number, duration: number, type: OscillatorType = 'sine', volume: number = 0.3) {
    if (!this.enabled) return;

    try {
      const ctx = this.getAudioContext();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.type = type;
      oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);

      gainNode.gain.setValueAtTime(volume, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + duration);
    } catch (e) {
      // 忽略音频错误
    }
  }

  // 播放和弦
  private playChord(frequencies: number[], duration: number, type: OscillatorType = 'sine', volume: number = 0.2) {
    frequencies.forEach(freq => this.playTone(freq, duration, type, volume));
  }

  // 升级音效
  playLevelUp() {
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((note, i) => {
      setTimeout(() => this.playTone(note, 0.3, 'square', 0.2), i * 150);
    });
  }

  // 获得装备音效
  playEquipment() {
    this.playTone(880, 0.15, 'square', 0.2);
    setTimeout(() => this.playTone(1108.73, 0.15, 'square', 0.2), 100);
    setTimeout(() => this.playTone(1318.51, 0.2, 'square', 0.2), 200);
  }

  // 获得经验值音效
  playExpGain() {
    this.playTone(659.25, 0.1, 'sine', 0.2);
    setTimeout(() => this.playTone(783.99, 0.1, 'sine', 0.2), 80);
  }

  // 获得金币音效
  playGoldGain() {
    this.playTone(1046.50, 0.08, 'triangle', 0.15);
    setTimeout(() => this.playTone(1318.51, 0.08, 'triangle', 0.15), 60);
  }

  // 完成任务音效
  playQuestComplete() {
    const notes = [523.25, 659.25, 783.99];
    notes.forEach((note, i) => {
      setTimeout(() => this.playTone(note, 0.2, 'square', 0.15), i * 100);
    });
  }

  // 获得称号音效
  playTitleEarned() {
    this.playChord([523.25, 659.25, 783.99], 0.3, 'sine', 0.15);
    setTimeout(() => this.playChord([659.25, 783.99, 1046.50], 0.4, 'sine', 0.15), 300);
  }

  // 按钮点击音效
  playClick() {
    this.playTone(800, 0.05, 'square', 0.1);
  }

  // 错误音效
  playError() {
    this.playTone(200, 0.2, 'sawtooth', 0.15);
    setTimeout(() => this.playTone(150, 0.3, 'sawtooth', 0.15), 150);
  }

  // 成就解锁音效
  playAchievement() {
    const notes = [783.99, 987.77, 1174.66, 1567.98]; // G5, B5, D6, G6
    notes.forEach((note, i) => {
      setTimeout(() => this.playTone(note, 0.25, 'square', 0.15), i * 120);
    });
  }

  // 属性提升音效
  playStatUp() {
    this.playTone(440, 0.1, 'sine', 0.15);
    setTimeout(() => this.playTone(554.37, 0.1, 'sine', 0.15), 80);
    setTimeout(() => this.playTone(659.25, 0.15, 'sine', 0.15), 160);
  }
}

export const soundManager = SoundManager.getInstance();

// 音效Hook
export function useSound() {
  return {
    playLevelUp: () => soundManager.playLevelUp(),
    playEquipment: () => soundManager.playEquipment(),
    playExpGain: () => soundManager.playExpGain(),
    playGoldGain: () => soundManager.playGoldGain(),
    playQuestComplete: () => soundManager.playQuestComplete(),
    playTitleEarned: () => soundManager.playTitleEarned(),
    playClick: () => soundManager.playClick(),
    playError: () => soundManager.playError(),
    playAchievement: () => soundManager.playAchievement(),
    playStatUp: () => soundManager.playStatUp(),
    isEnabled: () => soundManager.isEnabled(),
    setEnabled: (enabled: boolean) => soundManager.setEnabled(enabled)
  };
}