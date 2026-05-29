import { useState, useEffect } from 'react';
import './TimeDisplay.css';

interface TimeDisplayProps {
  showDate?: boolean;
  showSeconds?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export default function TimeDisplay({ 
  showDate = true, 
  showSeconds = true, 
  size = 'medium' 
}: TimeDisplayProps) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    
    if (showSeconds) {
      return `${hours}:${minutes}:${seconds}`;
    }
    return `${hours}:${minutes}`;
  };

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekDay = weekDays[date.getDay()];
    
    return `${year}年${month}月${day}日 ${weekDay}`;
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return '深夜了，注意休息';
    if (hour < 9) return '早上好，新的一天';
    if (hour < 12) return '上午好，精神饱满';
    if (hour < 14) return '中午好，记得吃饭';
    if (hour < 17) return '下午好，继续加油';
    if (hour < 19) return '傍晚好，辛苦了';
    if (hour < 22) return '晚上好，放松一下';
    return '夜深了，早点休息';
  };

  const getTimePeriod = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return '  深夜';
    if (hour < 9) return '  清晨';
    if (hour < 12) return '  上午';
    if (hour < 14) return '☀️ 中午';
    if (hour < 17) return '  下午';
    if (hour < 19) return '  傍晚';
    if (hour < 22) return '  晚上';
    return '  夜晚';
  };

  return (
    <div className={`time-display ${size}`}>
      <div className="time-period">{getTimePeriod()}</div>
      <div className="time-clock">
        <span className="time-digits">{formatTime(currentTime)}</span>
      </div>
      {showDate && (
        <div className="time-date">{formatDate(currentTime)}</div>
      )}
      <div className="time-greeting">{getGreeting()}</div>
    </div>
  );
}