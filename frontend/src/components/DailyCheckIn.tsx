import { useState, useEffect } from 'react';
import { checkIn, getCheckInStatus } from '../services/api';
import './DailyCheckIn.css';

interface DailyCheckInProps {
  characterId: number;
  onCheckIn: () => void;
}

interface CheckInStatus {
  checked_in_today: boolean;
  consecutive_days: number;
  month_checkins: string[];
}

function DailyCheckIn({ characterId, onCheckIn }: DailyCheckInProps) {
  const [status, setStatus] = useState<CheckInStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [result, setResult] = useState<{ message: string; reward_exp: number; reward_gold: number } | null>(null);

  useEffect(() => {
    loadStatus();
  }, [characterId]);

  const loadStatus = async () => {
    try {
      const data = await getCheckInStatus(characterId);
      setStatus(data);
    } catch (e) {
      console.error('加载签到状态失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async () => {
    setChecking(true);
    try {
      const res = await checkIn(characterId);
      if (res.success) {
        setResult({
          message: res.message,
          reward_exp: res.reward_exp,
          reward_gold: res.reward_gold
        });
        await loadStatus();
        onCheckIn();
        // 3秒后自动关闭
        setTimeout(() => {
          setShowPanel(false);
          setResult(null);
        }, 3000);
      } else {
        alert(res.message);
      }
    } catch (e) {
      console.error('签到失败:', e);
      alert('签到失败，请重试');
    } finally {
      setChecking(false);
    }
  };

  // 获取本月日历数据
  const getCalendarDays = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startWeekday = firstDay.getDay();

    const days = [];
    for (let i = 0; i < startWeekday; i++) {
      days.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }
    return days;
  };

  const isCheckedIn = (day: number) => {
    if (!status) return false;
    const today = new Date();
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return status.month_checkins.includes(dateStr);
  };

  const isToday = (day: number) => {
    const today = new Date();
    return day === today.getDate();
  };

  if (loading) return null;

  return (
    <>
      {/* 浮动签到按钮 */}
      <button 
        className={`checkin-fab ${status?.checked_in_today ? 'checked' : ''}`}
        onClick={() => setShowPanel(!showPanel)}
        title={status?.checked_in_today ? `已签到 ${status.consecutive_days} 天` : '点击签到'}
      >
        <span className="fab-icon">{status?.checked_in_today ? '✅' : ' '}</span>
        {status && status.consecutive_days > 0 && (
          <span className="fab-streak">{status.consecutive_days}</span>
        )}
      </button>

      {/* 签到面板 */}
      {showPanel && (
        <div className="checkin-panel-overlay" onClick={() => { setShowPanel(false); setResult(null); }}>
          <div className="checkin-panel" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header">
              <h3>  每日签到</h3>
              <button className="close-btn" onClick={() => { setShowPanel(false); setResult(null); }}>✕</button>
            </div>

            {/* 签到状态 */}
            <div className="panel-status">
              {status?.checked_in_today ? (
                <div className="status-checked">
                  <span className="status-icon">✅</span>
                  <span>今日已签到</span>
                  <span className="streak-count">连续 {status.consecutive_days} 天</span>
                </div>
              ) : (
                <div className="status-unchecked">
                  <span className="status-icon"> </span>
                  <span>今日未签到</span>
                </div>
              )}
            </div>

            {/* 签到结果 */}
            {result && (
              <div className="checkin-result">
                <div className="result-icon"> </div>
                <p className="result-msg">{result.message}</p>
                <div className="result-rewards">
                  <span className="reward-exp">⭐ +{result.reward_exp} 经验</span>
                  <span className="reward-gold">  +{result.reward_gold} 金币</span>
                </div>
                <div className="result-streak">
                  连续签到 {status?.consecutive_days || 1} 天
                </div>
              </div>
            )}

            {/* 签到按钮 */}
            {!status?.checked_in_today && !result && (
              <button 
                className="checkin-btn"
                onClick={handleCheckIn}
                disabled={checking}
              >
                <span className="btn-content">
                  {checking ? (
                    <>
                      <span className="btn-spinner"></span>
                      签到中...
                    </>
                  ) : (
                    <>
                      <span className="btn-icon">⚔️</span>
                      立即签到
                    </>
                  )}
                </span>
              </button>
            )}

            {/* 奖励预览 */}
            {!status?.checked_in_today && !result && (
              <div className="reward-preview">
                <div className="reward-preview-header">签到奖励</div>
                <div className="reward-preview-items">
                  <span className="reward-item">
                    <span className="reward-icon">⭐</span>
                    <span className="reward-value">{10 + (status?.consecutive_days || 0) * 5} EXP</span>
                  </span>
                  <span className="reward-item">
                    <span className="reward-icon"> </span>
                    <span className="reward-value">{5 + (status?.consecutive_days || 0) * 3}G</span>
                  </span>
                </div>
                {status?.consecutive_days && status.consecutive_days > 0 && (
                  <div className="reward-bonus">
                    连续签到加成 +{Math.min(status.consecutive_days * 10, 100)}%
                  </div>
                )}
              </div>
            )}

            {/* 迷你日历 */}
            <div className="mini-calendar">
              <div className="calendar-header">
                {new Date().getMonth() + 1}月
              </div>
              <div className="calendar-weekdays">
                <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
              </div>
              <div className="calendar-days">
                {getCalendarDays().map((day, index) => (
                  <div 
                    key={index} 
                    className={`day ${day ? '' : 'empty'} ${day && isCheckedIn(day) ? 'checked' : ''} ${day && isToday(day) ? 'today' : ''}`}
                  >
                    {day && (
                      <>
                        <span className="day-num">{day}</span>
                        {isCheckedIn(day) && <span className="day-check">✓</span>}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default DailyCheckIn;
