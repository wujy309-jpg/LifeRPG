import { useState, useEffect } from 'react';
import './AchievementPopup.css';

interface AchievementPopupProps {
  title: string;
  description: string;
  icon: string;
  onClose: () => void;
  autoClose?: boolean;
  duration?: number;
}

export default function AchievementPopup({ 
  title, 
  description, 
  icon, 
  onClose, 
  autoClose = true, 
  duration = 5000 
}: AchievementPopupProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    // 进入动画
    setTimeout(() => setIsVisible(true), 100);

    // 自动关闭
    if (autoClose) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [autoClose, duration]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 500);
  };

  return (
    <div className={`achievement-popup ${isVisible ? 'visible' : ''} ${isClosing ? 'closing' : ''}`}>
      <div className="achievement-glow"></div>
      <div className="achievement-content">
        <div className="achievement-icon-wrapper">
          <div className="achievement-icon">{icon}</div>
          <div className="achievement-sparkles">
            <span className="sparkle">✦</span>
            <span className="sparkle">✦</span>
            <span className="sparkle">✦</span>
            <span className="sparkle">✦</span>
          </div>
        </div>
        <div className="achievement-info">
          <span className="achievement-label">成就解锁！</span>
          <h3 className="achievement-title">{title}</h3>
          <p className="achievement-description">{description}</p>
        </div>
        <button className="achievement-close" onClick={handleClose}>×</button>
      </div>
    </div>
  );
}