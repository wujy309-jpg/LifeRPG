import { useMemo } from 'react';
import type { ActivityHistory } from '../services/api';
import './ActivityChart.css';

interface ActivityChartProps {
  data: ActivityHistory[];
  days: number;
}

export default function ActivityChart({ data, days }: ActivityChartProps) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // 反转数据使其按日期正序
    const reversed = [...data].reverse();
    
    // 计算最大值用于缩放
    const maxCount = Math.max(...reversed.map(d => d.count), 1);
    const maxExp = Math.max(...reversed.map(d => d.exp), 1);
    
    return reversed.map(item => ({
      ...item,
      countHeight: (item.count / maxCount) * 100,
      expHeight: (item.exp / maxExp) * 100,
      shortDate: item.date.substring(5) // MM-DD
    }));
  }, [data]);

  const totalActivities = useMemo(() => {
    return data.reduce((sum, d) => sum + d.count, 0);
  }, [data]);

  const totalExp = useMemo(() => {
    return data.reduce((sum, d) => sum + d.exp, 0);
  }, [data]);

  const avgActivities = useMemo(() => {
    return data.length > 0 ? (totalActivities / data.length).toFixed(1) : '0';
  }, [data, totalActivities]);

  if (!data || data.length === 0) {
    return (
      <div className="activity-chart">
        <div className="chart-empty">暂无活动数据</div>
      </div>
    );
  }

  return (
    <div className="activity-chart">
      {/* 图表统计 */}
      <div className="chart-stats">
        <div className="chart-stat">
          <span className="stat-label">总活动次数</span>
          <span className="stat-value">{totalActivities}</span>
        </div>
        <div className="chart-stat">
          <span className="stat-label">总经验值</span>
          <span className="stat-value">{totalExp.toLocaleString()}</span>
        </div>
        <div className="chart-stat">
          <span className="stat-label">日均活动</span>
          <span className="stat-value">{avgActivities}</span>
        </div>
      </div>

      {/* 柱状图 */}
      <div className="chart-container">
        <div className="chart-y-axis">
          <span>{Math.max(...data.map(d => d.count))}</span>
          <span>{Math.round(Math.max(...data.map(d => d.count)) / 2)}</span>
          <span>0</span>
        </div>
        <div className="chart-bars">
          {chartData.map((item, index) => (
            <div key={item.date} className="bar-group">
              <div className="bar-wrapper">
                <div 
                  className="bar count-bar" 
                  style={{ height: `${item.countHeight}%` }}
                  title={`${item.shortDate}: ${item.count}次活动`}
                >
                  {item.count > 0 && (
                    <span className="bar-tooltip">{item.count}</span>
                  )}
                </div>
              </div>
              {(index % Math.ceil(days / 7) === 0 || index === chartData.length - 1) && (
                <span className="bar-label">{item.shortDate}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 图例 */}
      <div className="chart-legend">
        <div className="legend-item">
          <div className="legend-color count-color"></div>
          <span>活动次数</span>
        </div>
      </div>
    </div>
  );
}