import { useState, useEffect } from 'react';
import { getActivityStats, getActivityHistory, getAttributeHistory, getWeeklyActivityTypes } from '../services/api';
import type { ActivityStats, ActivityHistory, AttributeHistory } from '../services/api';
import ActivityChart from './ActivityChart';
import AttributeChart from './AttributeChart';
import './StatsPanel.css';

interface StatsPanelProps {
  characterId: number;
}

export default function StatsPanel({ characterId }: StatsPanelProps) {
  const [stats, setStats] = useState<ActivityStats | null>(null);
  const [activityHistory, setActivityHistory] = useState<ActivityHistory[]>([]);
  const [attributeHistory, setAttributeHistory] = useState<AttributeHistory[]>([]);
  const [weeklyTypes, setWeeklyTypes] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<7 | 14 | 30>(30);

  useEffect(() => {
    loadStats();
  }, [characterId, timeRange]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [statsData, historyData, attrData, typesData] = await Promise.all([
        getActivityStats(characterId),
        getActivityHistory(characterId, timeRange),
        getAttributeHistory(characterId, timeRange),
        getWeeklyActivityTypes(characterId)
      ]);
      setStats(statsData);
      setActivityHistory(historyData);
      setAttributeHistory(attrData);
      setWeeklyTypes(typesData);
    } catch (e) {
      console.error('加载统计数据失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const getActivityTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      '学习': ' ',
      '运动': ' ️',
      '编程': '  ',
      '社交': ' ',
      '工作': ' ',
      '创作': ' ',
      '生活': ' ',
      '休息': ' '
    };
    return icons[type] || ' ';
  };

  const getActivityTypeName = (type: string) => {
    const names: Record<string, string> = {
      '学习': '学习',
      '运动': '运动',
      '编程': '编程',
      '社交': '社交',
      '工作': '工作',
      '创作': '创作',
      '生活': '生活',
      '休息': '休息'
    };
    return names[type] || type;
  };

  if (loading) {
    return <div className="loading">加载统计数据...</div>;
  }

  if (!stats) {
    return <div className="loading">无法加载统计数据</div>;
  }

  return (
    <div className="stats-panel">
      <header className="stats-header">
        <h2>  数据统计</h2>
        <div className="time-range-selector">
          <button 
            className={`range-btn ${timeRange === 7 ? 'active' : ''}`}
            onClick={() => setTimeRange(7)}
          >
            7天
          </button>
          <button 
            className={`range-btn ${timeRange === 14 ? 'active' : ''}`}
            onClick={() => setTimeRange(14)}
          >
            14天
          </button>
          <button 
            className={`range-btn ${timeRange === 30 ? 'active' : ''}`}
            onClick={() => setTimeRange(30)}
          >
            30天
          </button>
        </div>
      </header>

      {/* 统计卡片 */}
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon"> </div>
          <div className="stat-info">
            <span className="stat-value">{stats.total_count}</span>
            <span className="stat-label">总活动次数</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"> </div>
          <div className="stat-info">
            <span className="stat-value">{stats.today_count}</span>
            <span className="stat-label">今日活动</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"> </div>
          <div className="stat-info">
            <span className="stat-value">{stats.week_count}</span>
            <span className="stat-label">本周活动</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"> ️</div>
          <div className="stat-info">
            <span className="stat-value">{stats.consecutive_days}</span>
            <span className="stat-label">连续天数</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-info">
            <span className="stat-value">{stats.total_exp.toLocaleString()}</span>
            <span className="stat-label">总经验值</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"> </div>
          <div className="stat-info">
            <span className="stat-value">{stats.total_gold.toLocaleString()}</span>
            <span className="stat-label">总金币</span>
          </div>
        </div>
      </div>

      {/* 活动类型统计 */}
      <div className="type-stats-section">
        <h3>  活动类型分布</h3>
        <div className="type-stats-grid">
          {stats.type_stats.map(type => (
            <div key={type.activity_type} className="type-stat-item">
              <span className="type-icon">{getActivityTypeIcon(type.activity_type)}</span>
              <span className="type-name">{getActivityTypeName(type.activity_type)}</span>
              <span className="type-count">{type.count}次</span>
              <div className="type-bar">
                <div 
                  className="type-bar-fill" 
                  style={{ width: `${(type.count / stats.total_count) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
        {stats.most_common && (
          <div className="most-common">
            最常做的活动：<strong>{getActivityTypeIcon(stats.most_common)} {getActivityTypeName(stats.most_common)}</strong>
          </div>
        )}
      </div>

      {/* 活动历史图表 */}
      <div className="chart-section">
        <h3>  活动趋势</h3>
        <ActivityChart data={activityHistory} days={timeRange} />
      </div>

      {/* 属性成长曲线 */}
      <div className="chart-section">
        <h3>  属性成长曲线</h3>
        <AttributeChart data={attributeHistory} days={timeRange} />
      </div>

      {/* 本周活动类型 */}
      <div className="weekly-types-section">
        <h3>  本周活动类型</h3>
        <div className="weekly-types-grid">
          {Object.entries(weeklyTypes).map(([type, count]) => (
            <div key={type} className="weekly-type-item">
              <span className="type-icon">{getActivityTypeIcon(type)}</span>
              <span className="type-name">{getActivityTypeName(type)}</span>
              <span className="type-count">{count}次</span>
            </div>
          ))}
          {Object.keys(weeklyTypes).length === 0 && (
            <div className="no-data">本周还没有活动记录</div>
          )}
        </div>
      </div>
    </div>
  );
}