import { useState, useEffect } from 'react';
import './Calendar.css';

interface CalendarProps {
  onDateSelect?: (date: Date) => void;
  selectedDate?: Date;
}

export default function Calendar({ onDateSelect, selectedDate }: CalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewDate, setViewDate] = useState(new Date());
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDate(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();
  const startDay = firstDayOfMonth.getDay();

  const prevMonth = () => {
    setViewDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setViewDate(new Date(year, month + 1, 1));
  };

  const goToToday = () => {
    setViewDate(new Date());
    if (onDateSelect) {
      onDateSelect(new Date());
    }
  };

  const isToday = (day: number) => {
    const today = currentDate;
    return day === today.getDate() && 
           month === today.getMonth() && 
           year === today.getFullYear();
  };

  const isSelected = (day: number) => {
    if (!selectedDate) return false;
    return day === selectedDate.getDate() && 
           month === selectedDate.getMonth() && 
           year === selectedDate.getFullYear();
  };

  const handleDateClick = (day: number) => {
    const selected = new Date(year, month, day);
    if (onDateSelect) {
      onDateSelect(selected);
    }
  };

  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];

  const renderDays = () => {
    const days = [];
    
    // 空白天数（月初前）
    for (let i = 0; i < startDay; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }
    
    // 月份天数
    for (let day = 1; day <= daysInMonth; day++) {
      const today = isToday(day);
      const selected = isSelected(day);
      const isWeekend = new Date(year, month, day).getDay() === 0 || 
                        new Date(year, month, day).getDay() === 6;
      
      days.push(
        <div
          key={day}
          className={`calendar-day ${today ? 'today' : ''} ${selected ? 'selected' : ''} ${isWeekend ? 'weekend' : ''}`}
          onClick={() => handleDateClick(day)}
        >
          <span className="day-number">{day}</span>
          {today && <span className="today-dot"></span>}
        </div>
      );
    }
    
    return days;
  };

  const getMonthName = (month: number) => {
    const months = ['一月', '二月', '三月', '四月', '五月', '六月', 
                    '七月', '八月', '九月', '十月', '十一月', '十二月'];
    return months[month];
  };

  return (
    <div className={`calendar-container ${collapsed ? 'collapsed' : ''}`}>
      <div className="calendar-header">
        <button className="nav-btn" onClick={prevMonth}>‹</button>
        <div className="month-year">
          <span className="month">{getMonthName(month)}</span>
          <span className="year">{year}</span>
        </div>
        <button className="nav-btn" onClick={nextMonth}>›</button>
        <button 
          className="collapse-btn" 
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? '展开日历' : '收起日历'}
        >
          {collapsed ? '▼' : '▲'}
        </button>
      </div>
      
      {!collapsed && (
        <>
          <div className="calendar-weekdays">
            {weekDays.map(day => (
              <div key={day} className="weekday">{day}</div>
            ))}
          </div>
          
          <div className="calendar-days">
            {renderDays()}
          </div>
          
          <div className="calendar-footer">
            <button className="today-btn" onClick={goToToday}>
                回到今天
            </button>
          </div>
        </>
      )}
    </div>
  );
}