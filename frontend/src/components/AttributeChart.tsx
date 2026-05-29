import { useMemo } from 'react';
import type { AttributeHistory } from '../services/api';
import './AttributeChart.css';

interface AttributeChartProps {
  data: AttributeHistory[];
  days: number;
}

const ATTR_CONFIG = {
  strength: { name: '力量', color: '#ef4444', icon: ' ' },
  intelligence: { name: '智力', color: '#3b82f6', icon: ' ' },
  agility: { name: '敏捷', color: '#22c55e', icon: '⚡' },
  charisma: { name: '魅力', color: '#a855f7', icon: ' ' },
  willpower: { name: '意志', color: '#f59e0b', icon: ' ' }
};

export default function AttributeChart({ data }: AttributeChartProps) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null;
    
    const reversed = [...data].reverse();
    
    // 计算每个属性的范围
    const ranges: Record<string, { min: number; max: number }> = {};
    Object.keys(ATTR_CONFIG).forEach(attr => {
      const values = reversed.map(d => (d as any)[attr] || 0);
      ranges[attr] = {
        min: Math.min(...values),
        max: Math.max(...values)
      };
    });
    
    return { reversed, ranges };
  }, [data]);

  const currentStats = useMemo(() => {
    if (!data || data.length === 0) return null;
    return data[0]; // 最新的数据
  }, [data]);

  const changes = useMemo(() => {
    if (!data || data.length < 2) return {};
    
    const latest = data[0];
    const oldest = data[data.length - 1];
    
    const result: Record<string, number> = {};
    Object.keys(ATTR_CONFIG).forEach(attr => {
      result[attr] = ((latest as any)[attr] || 0) - ((oldest as any)[attr] || 0);
    });
    return result;
  }, [data]);

  if (!data || data.length === 0 || !chartData || !currentStats) {
    return (
      <div className="attribute-chart">
        <div className="chart-empty">暂无属性数据</div>
      </div>
    );
  }

  const renderAttributeLine = (attr: string) => {
    const config = ATTR_CONFIG[attr as keyof typeof ATTR_CONFIG];
    const { reversed, ranges } = chartData;
    const range = ranges[attr];
    const rangeSize = range.max - range.min || 1;
    
    // 生成SVG路径
    const width = 100;
    const height = 100;
    const points = reversed.map((d, i) => {
      const x = (i / (reversed.length - 1)) * width;
      const y = height - (((d as any)[attr] - range.min) / rangeSize) * height;
      return `${x},${y}`;
    });
    
    const path = `M ${points.join(' L ')}`;
    const change = changes[attr] || 0;
    
    return (
      <div key={attr} className="attribute-line">
        <div className="attr-header">
          <span className="attr-icon">{config.icon}</span>
          <span className="attr-name">{config.name}</span>
          <span className="attr-value">{(currentStats as any)[attr]}</span>
          {change !== 0 && (
            <span className={`attr-change ${change > 0 ? 'positive' : 'negative'}`}>
              {change > 0 ? '+' : ''}{change}
            </span>
          )}
        </div>
        <div className="attr-chart-container">
          <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
            {/* 背景网格 */}
            <line x1="0" y1="25" x2={width} y2="25" stroke="var(--border-dark)" strokeWidth="0.5" />
            <line x1="0" y1="50" x2={width} y2="50" stroke="var(--border-dark)" strokeWidth="0.5" />
            <line x1="0" y1="75" x2={width} y2="75" stroke="var(--border-dark)" strokeWidth="0.5" />
            
            {/* 属性曲线 */}
            <path
              d={path}
              fill="none"
              stroke={config.color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            
            {/* 最新值点 */}
            <circle
              cx={width}
              cy={height - (((currentStats as any)[attr] - range.min) / rangeSize) * height}
              r="3"
              fill={config.color}
            />
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="attribute-chart">
      {/* 属性卡片 */}
      <div className="attr-cards">
        {Object.keys(ATTR_CONFIG).map(attr => {
          const config = ATTR_CONFIG[attr as keyof typeof ATTR_CONFIG];
          const value = (currentStats as any)[attr];
          const change = changes[attr] || 0;
          
          return (
            <div key={attr} className="attr-card">
              <div className="attr-card-icon" style={{ color: config.color }}>{config.icon}</div>
              <div className="attr-card-info">
                <span className="attr-card-name">{config.name}</span>
                <span className="attr-card-value">{value}</span>
              </div>
              {change !== 0 && (
                <span className={`attr-card-change ${change > 0 ? 'positive' : 'negative'}`}>
                  {change > 0 ? '↑' : '↓'}{Math.abs(change)}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* 属性曲线图 */}
      <div className="attr-lines">
        {Object.keys(ATTR_CONFIG).map(attr => renderAttributeLine(attr))}
      </div>

      {/* 图例 */}
      <div className="attr-legend">
        {Object.entries(ATTR_CONFIG).map(([key, config]) => (
          <div key={key} className="legend-item">
            <div className="legend-color" style={{ background: config.color }}></div>
            <span>{config.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}