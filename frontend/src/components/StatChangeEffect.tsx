import { useEffect, useState, useRef } from 'react';
import './StatChangeEffect.css';

interface StatChangeEffectProps {
  changes: Record<string, number>;
  stats: Record<string, { name: string; icon: string; value: number }>;
  onComplete: () => void;
}

function StatChangeEffect({ changes, stats, onComplete }: StatChangeEffectProps) {
  const [visible, setVisible] = useState(true);
  const [animatedValues, setAnimatedValues] = useState<Record<string, number>>({});
  const animationRef = useRef<number>(0);

  useEffect(() => {
    // 初始化动画值
    const initialValues: Record<string, number> = {};
    Object.keys(changes).forEach(attr => {
      const stat = stats[attr];
      if (stat) {
        initialValues[attr] = stat.value - changes[attr];
      }
    });
    setAnimatedValues(initialValues);

    // 动画目标值
    const targetValues: Record<string, number> = {};
    Object.keys(changes).forEach(attr => {
      const stat = stats[attr];
      if (stat) {
        targetValues[attr] = stat.value;
      }
    });

    // 执行动画
    const startTime = Date.now();
    const duration = 800;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // 缓动函数
      const eased = 1 - Math.pow(1 - progress, 3);

      const currentValues: Record<string, number> = {};
      Object.keys(initialValues).forEach(attr => {
        const start = initialValues[attr];
        const end = targetValues[attr];
        currentValues[attr] = Math.round(start + (end - start) * eased);
      });
      setAnimatedValues(currentValues);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // 动画完成，延迟后隐藏
        setTimeout(() => {
          setVisible(false);
          setTimeout(onComplete, 300);
        }, 1000);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [changes, stats, onComplete]);

  if (!visible) return null;

  return (
    <div className="stat-change-overlay">
      <div className="stat-change-container">
        <h3 className="stat-change-title">属性提升</h3>
        <div className="stat-changes-list">
          {Object.entries(changes).map(([attr, gain]) => {
            const stat = stats[attr];
            if (!stat || gain === 0) return null;

            return (
              <div key={attr} className="stat-change-item">
                <div className="stat-info">
                  <span className="stat-icon">{stat.icon}</span>
                  <span className="stat-name">{stat.name}</span>
                </div>
                <div className="stat-progress">
                  <div className="stat-values">
                    <span className="old-value">{animatedValues[attr] ?? stat.value - gain}</span>
                    <span className="arrow">→</span>
                    <span className="new-value">{stat.value}</span>
                  </div>
                  <div className="gain-badge">+{gain}</div>
                </div>
                <div className="stat-bar-container">
                  <div 
                    className="stat-bar-fill"
                    style={{ width: `${(animatedValues[attr] ?? stat.value) / 100 * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default StatChangeEffect;
