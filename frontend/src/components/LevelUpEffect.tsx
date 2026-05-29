import { useEffect, useState } from 'react';
import './LevelUpEffect.css';

interface LevelUpEffectProps {
  show: boolean;
  newLevel: number;
  onClose: () => void;
}

function LevelUpEffect({ show, newLevel, onClose }: LevelUpEffectProps) {
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; delay: number }>>([]);

  useEffect(() => {
    if (show) {
      // 生成粒子
      const newParticles = Array.from({ length: 30 }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 0.5
      }));
      setParticles(newParticles);

      // 3秒后自动关闭
      const timer = setTimeout(() => {
        onClose();
      }, 3500);

      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!show) return null;

  return (
    <div className="level-up-overlay" onClick={onClose}>
      {/* 粒子效果 */}
      <div className="particles-container">
        {particles.map(p => (
          <div
            key={p.id}
            className="particle"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              animationDelay: `${p.delay}s`
            }}
          />
        ))}
      </div>

      {/* 主内容 */}
      <div className="level-up-content">
        {/* 光环效果 */}
        <div className="glow-ring" />
        <div className="glow-ring delay-1" />
        <div className="glow-ring delay-2" />

        {/* 升级文字 */}
        <div className="level-up-text">
          <span className="level-up-label">LEVEL UP!</span>
        </div>

        {/* 新等级 */}
        <div className="new-level-container">
          <div className="level-badge">
            <span className="level-number">{newLevel}</span>
          </div>
        </div>

        {/* 恭喜文字 */}
        <div className="congrats-text">
          <p>恭喜达到 <span className="highlight">Lv.{newLevel}</span></p>
          <p className="subtitle">{getLevelTitle(newLevel)}</p>
        </div>

        {/* 奖励 */}
        <div className="rewards-container">
          <div className="reward-item">
            <span className="reward-icon"> </span>
            <span className="reward-text">+3 属性点</span>
          </div>
          <div className="reward-item">
            <span className="reward-icon"> </span>
            <span className="reward-text">+{newLevel * 10} 金币</span>
          </div>
        </div>

        {/* 点击关闭提示 */}
        <div className="close-hint">点击任意位置关闭</div>
      </div>
    </div>
  );
}

function getLevelTitle(level: number): string {
  if (level < 5) return "新手冒险者";
  if (level < 10) return "初级勇者";
  if (level < 20) return "中级战士";
  if (level < 30) return "高级英雄";
  if (level < 50) return "传奇大师";
  return "不朽传说";
}

export default LevelUpEffect;
