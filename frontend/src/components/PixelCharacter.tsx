import { useEffect, useRef } from 'react';
import './PixelCharacter.css';

interface PixelCharacterProps {
  size?: number;
  animate?: boolean;
  className?: string;
  score?: number; // 属性分数，用于显示边框颜色
}

// 根据总属性(平均值)获取边框颜色和样式
// 总属性范围：0-100，初始约50-65，通过游戏慢慢提升
function getFrameStyle(score: number): { color: string; glow: string; name: string; shadow: string } {
  if (score >= 90) {
    return { 
      color: '#ef4444', 
      glow: '0 0 8px #ef4444, 0 0 16px #ef4444, 0 0 24px rgba(239,68,68,0.5)', 
      name: 'red',
      shadow: '0 0 30px rgba(239,68,68,0.6), inset 0 0 15px rgba(239,68,68,0.3)'
    }; // 红色框 - 90+
  } else if (score >= 80) {
    return { 
      color: '#f59e0b', 
      glow: '0 0 8px #f59e0b, 0 0 16px #f59e0b, 0 0 20px rgba(245,158,11,0.4)', 
      name: 'gold',
      shadow: '0 0 25px rgba(245,158,11,0.5), inset 0 0 12px rgba(245,158,11,0.2)'
    }; // 金色框 - 80-89
  } else if (score >= 70) {
    return { 
      color: '#a855f7', 
      glow: '0 0 6px #a855f7, 0 0 12px #a855f7, 0 0 18px rgba(168,85,247,0.4)', 
      name: 'purple',
      shadow: '0 0 20px rgba(168,85,247,0.4), inset 0 0 10px rgba(168,85,247,0.2)'
    }; // 紫色框 - 70-79
  } else if (score >= 60) {
    return { 
      color: '#3b82f6', 
      glow: '0 0 6px #3b82f6, 0 0 12px #3b82f6, 0 0 16px rgba(59,130,246,0.3)', 
      name: 'blue',
      shadow: '0 0 18px rgba(59,130,246,0.4), inset 0 0 8px rgba(59,130,246,0.2)'
    }; // 蓝色框 - 60-69
  } else if (score >= 50) {
    return { 
      color: '#22c55e', 
      glow: '0 0 5px #22c55e, 0 0 10px rgba(34,197,94,0.4)', 
      name: 'green',
      shadow: '0 0 15px rgba(34,197,94,0.3), inset 0 0 6px rgba(34,197,94,0.15)'
    }; // 绿色框 - 50-59
  } else if (score >= 40) {
    return { 
      color: '#ffffff', 
      glow: '0 0 5px #ffffff, 0 0 10px rgba(255,255,255,0.3)', 
      name: 'white',
      shadow: '0 0 12px rgba(255,255,255,0.3), inset 0 0 5px rgba(255,255,255,0.1)'
    }; // 白色框 - 40-49
  }
  return { color: 'transparent', glow: 'none', name: 'none', shadow: 'none' }; // 无边框 - <40
}

// 像素小人精灵图数据
// 16x16 像素角色
const PIXEL_DATA = [
  // 头发 (棕色)
  { x: 5, y: 0, w: 6, h: 1, color: '#8B4513' },
  { x: 4, y: 1, w: 8, h: 1, color: '#8B4513' },
  { x: 4, y: 2, w: 8, h: 1, color: '#8B4513' },
  
  // 脸部 (肤色)
  { x: 5, y: 3, w: 6, h: 1, color: '#FFDAB9' },
  { x: 5, y: 4, w: 6, h: 1, color: '#FFDAB9' },
  { x: 5, y: 5, w: 6, h: 1, color: '#FFDAB9' },
  { x: 5, y: 6, w: 6, h: 1, color: '#FFDAB9' },
  
  // 眼睛 (黑色)
  { x: 6, y: 4, w: 1, h: 1, color: '#000000' },
  { x: 9, y: 4, w: 1, h: 1, color: '#000000' },
  
  // 嘴巴 (红色)
  { x: 7, y: 5, w: 2, h: 1, color: '#FF6B6B' },
  
  // 身体 (盔甲 - 蓝色)
  { x: 4, y: 7, w: 8, h: 1, color: '#4169E1' },
  { x: 3, y: 8, w: 10, h: 1, color: '#4169E1' },
  { x: 3, y: 9, w: 10, h: 1, color: '#4169E1' },
  { x: 3, y: 10, w: 10, h: 1, color: '#4169E1' },
  { x: 4, y: 11, w: 8, h: 1, color: '#4169E1' },
  
  // 盔甲细节 (金色)
  { x: 7, y: 7, w: 2, h: 1, color: '#FFD700' },
  { x: 7, y: 8, w: 2, h: 1, color: '#FFD700' },
  
  // 手臂 (肤色)
  { x: 2, y: 8, w: 1, h: 2, color: '#FFDAB9' },
  { x: 13, y: 8, w: 1, h: 2, color: '#FFDAB9' },
  
  // 手 (肤色)
  { x: 1, y: 9, w: 1, h: 1, color: '#FFDAB9' },
  { x: 14, y: 9, w: 1, h: 1, color: '#FFDAB9' },
  
  // 腿 (深蓝)
  { x: 5, y: 12, w: 2, h: 1, color: '#1E3A8A' },
  { x: 9, y: 12, w: 2, h: 1, color: '#1E3A8A' },
  { x: 5, y: 13, w: 2, h: 1, color: '#1E3A8A' },
  { x: 9, y: 13, w: 2, h: 1, color: '#1E3A8A' },
  
  // 靴子 (棕色)
  { x: 4, y: 14, w: 3, h: 1, color: '#654321' },
  { x: 9, y: 14, w: 3, h: 1, color: '#654321' },
  { x: 4, y: 15, w: 3, h: 1, color: '#654321' },
  { x: 9, y: 15, w: 3, h: 1, color: '#654321' },
  
  // 剑 (银色)
  { x: 15, y: 6, w: 1, h: 1, color: '#C0C0C0' },
  { x: 15, y: 7, w: 1, h: 1, color: '#C0C0C0' },
  { x: 15, y: 8, w: 1, h: 1, color: '#C0C0C0' },
  { x: 15, y: 9, w: 1, h: 1, color: '#C0C0C0' },
  { x: 15, y: 10, w: 1, h: 1, color: '#C0C0C0' },
  { x: 15, y: 11, w: 1, h: 1, color: '#C0C0C0' },
  
  // 剑柄 (金色)
  { x: 14, y: 6, w: 1, h: 1, color: '#FFD700' },
  { x: 16, y: 6, w: 1, h: 1, color: '#FFD700' },
];

function PixelCharacter({ size = 64, animate = true, className, score }: PixelCharacterProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  // 计算边框样式
  const frameStyle = score !== undefined ? getFrameStyle(score) : null;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布大小
    const pixelSize = size / 16;
    canvas.width = size;
    canvas.height = size;

    // 清除画布
    ctx.clearRect(0, 0, size, size);

    // 绘制像素
    const drawFrame = (bounce: number) => {
      ctx.clearRect(0, 0, size, size);

      PIXEL_DATA.forEach(pixel => {
        ctx.fillStyle = pixel.color;
        ctx.fillRect(
          pixel.x * pixelSize,
          (pixel.y + bounce) * pixelSize,
          pixel.w * pixelSize,
          pixel.h * pixelSize
        );
      });
    };

    if (animate) {
      // 动画循环
      let startTime = Date.now();
      const animateLoop = () => {
        const elapsed = Date.now() - startTime;
        const bounce = Math.sin(elapsed / 300) * 0.5;
        drawFrame(bounce);
        animRef.current = requestAnimationFrame(animateLoop);
      };
      animRef.current = requestAnimationFrame(animateLoop);

      return () => {
        if (animRef.current) {
          cancelAnimationFrame(animRef.current);
        }
      };
    } else {
      drawFrame(0);
    }
  }, [size, animate]);

  // 构建容器样式
  const containerStyle: React.CSSProperties = frameStyle && frameStyle.name !== 'none' ? {
    display: 'inline-block',
    padding: '4px',
    border: `3px solid ${frameStyle.color}`,
    borderRadius: '8px',
    boxShadow: frameStyle.glow,
    background: 'rgba(0, 0, 0, 0.5)',
    position: 'relative',
  } : {};

  return (
    <div 
      className={`pixel-character-frame ${frameStyle?.name || ''} ${className || ''}`} 
      style={containerStyle}
    >
      <canvas
        ref={canvasRef}
        className="pixel-character"
        style={{ width: size, height: size, imageRendering: 'pixelated' }}
      />
      {/* 外层光晕 */}
      {frameStyle && frameStyle.name !== 'none' && (
        <div 
          className="frame-glow"
          style={{
            position: 'absolute',
            top: '-4px',
            left: '-4px',
            right: '-4px',
            bottom: '-4px',
            borderRadius: '12px',
            boxShadow: frameStyle.shadow,
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  );
}

export default PixelCharacter;
