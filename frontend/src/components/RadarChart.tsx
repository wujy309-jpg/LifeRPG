import { useEffect, useRef } from 'react';
import './RadarChart.css';

interface RadarChartProps {
  stats: {
    strength: number;
    intelligence: number;
    agility: number;
    charisma: number;
    willpower: number;
  };
  size?: number;
  showLabels?: boolean;
  showValues?: boolean;
  animated?: boolean;
}

const LABELS = [
  { key: 'strength', label: '力量', icon: ' ', color: '#ff6b6b' },
  { key: 'intelligence', label: '智力', icon: ' ', color: '#4ecdc4' },
  { key: 'agility', label: '敏捷', icon: ' ', color: '#45b7d1' },
  { key: 'charisma', label: '魅力', icon: ' ', color: '#f9ca24' },
  { key: 'willpower', label: '意志', icon: ' ️', color: '#a55eea' },
];

function RadarChart({
  stats,
  size = 280,
  showLabels = true,
  showValues = true,
  animated = true
}: RadarChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const progressRef = useRef(0);

  const center = size / 2;
  const radius = size / 2 - 50;
  const maxValue = 100; // 属性最大值为100

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置高清屏支持
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    if (animated) {
      progressRef.current = 0;
      animate(ctx);
    } else {
      progressRef.current = 1;
      draw(ctx, 1);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [stats, size, animated]);

  const animate = (ctx: CanvasRenderingContext2D) => {
    const duration = 1000; // 1秒动画
    const startTime = Date.now();

    const frame = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // 缓动函数
      const eased = 1 - Math.pow(1 - progress, 3);
      progressRef.current = eased;

      ctx.clearRect(0, 0, size, size);
      draw(ctx, eased);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(frame);
      }
    };

    frame();
  };

  const getPoint = (index: number, value: number, progress: number) => {
    const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
    const r = (value / maxValue) * radius * progress;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle)
    };
  };

  const draw = (ctx: CanvasRenderingContext2D, progress: number) => {
    const values = LABELS.map(l => stats[l.key as keyof typeof stats]);

    // 绘制背景网格
    drawGrid(ctx);

    // 绘制数据区域
    drawDataArea(ctx, values, progress);

    // 绘制数据点
    drawDataPoints(ctx, values, progress);

    // 绘制标签
    if (showLabels) {
      drawLabels(ctx);
    }

    // 绘制数值
    if (showValues) {
      drawValues(ctx, values, progress);
    }
  };

  const drawGrid = (ctx: CanvasRenderingContext2D) => {
    const levels = 5;

    for (let level = 1; level <= levels; level++) {
      const r = (level / levels) * radius;

      ctx.beginPath();
      for (let i = 0; i <= 5; i++) {
        const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();
      ctx.strokeStyle = `rgba(255, 255, 255, ${0.05 + level * 0.03})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // 绘制从中心到顶点的线
    for (let i = 0; i < 5; i++) {
      const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
      const x = center + radius * Math.cos(angle);
      const y = center + radius * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.lineTo(x, y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  };

  const drawDataArea = (ctx: CanvasRenderingContext2D, values: number[], progress: number) => {
    ctx.beginPath();

    values.forEach((value, index) => {
      const point = getPoint(index, value, progress);
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });

    ctx.closePath();

    // 渐变填充
    const gradient = ctx.createRadialGradient(center, center, 0, center, center, radius);
    gradient.addColorStop(0, 'rgba(108, 92, 231, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 206, 201, 0.2)');
    ctx.fillStyle = gradient;
    ctx.fill();

    // 边框
    ctx.strokeStyle = 'rgba(108, 92, 231, 0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();
  };

  const drawDataPoints = (ctx: CanvasRenderingContext2D, values: number[], progress: number) => {
    values.forEach((value, index) => {
      const point = getPoint(index, value, progress);
      const label = LABELS[index];

      // 外圈光晕
      ctx.beginPath();
      ctx.arc(point.x, point.y, 8, 0, Math.PI * 2);
      ctx.fillStyle = label.color + '40';
      ctx.fill();

      // 内圈
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = label.color;
      ctx.fill();

      // 白色中心
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = '#fff';
      ctx.fill();
    });
  };

  const drawLabels = (ctx: CanvasRenderingContext2D) => {
    const labelRadius = radius + 30;

    LABELS.forEach((label, index) => {
      const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
      const x = center + labelRadius * Math.cos(angle);
      const y = center + labelRadius * Math.sin(angle);

      ctx.font = '14px "Segoe UI", "Microsoft YaHei", sans-serif';
      ctx.fillStyle = label.color;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // 根据位置调整
      if (index === 0) { // 顶部
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
      } else if (index === 1 || index === 2) { // 右侧
        ctx.textAlign = 'left';
      } else if (index === 3 || index === 4) { // 左侧
        ctx.textAlign = 'right';
      }

      ctx.fillText(`${label.label}`, x, y);
    });
  };

  const drawValues = (ctx: CanvasRenderingContext2D, values: number[], progress: number) => {
    values.forEach((value, index) => {
      const point = getPoint(index, value, progress);
      const label = LABELS[index];

      // 计算文字位置（往外偏移一点）
      const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
      const offsetX = 15 * Math.cos(angle);
      const offsetY = 15 * Math.sin(angle);

      ctx.font = 'bold 12px "Segoe UI", monospace';
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // 背景框
      const text = Math.round(value * progress).toString();
      const textWidth = ctx.measureText(text).width;
      const px = point.x + offsetX;
      const py = point.y + offsetY;

      ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
      ctx.beginPath();
      // 使用普通矩形，兼容性更好
      ctx.rect(px - textWidth/2 - 4, py - 8, textWidth + 8, 16);
      ctx.fill();

      ctx.fillStyle = label.color;
      ctx.fillText(text, px, py);
    });
  };

  const totalStats = Math.round(Object.values(stats).reduce((a, b) => a + b, 0) / 5);

  return (
    <div className="radar-chart-container">
      <canvas
        ref={canvasRef}
        className="radar-chart-canvas"
        style={{ width: size, height: size }}
      />
      <div className="radar-chart-center">
        <span className="center-value">{totalStats}</span>
        <span className="center-label">总属性</span>
      </div>
    </div>
  );
}

export default RadarChart;
