import { useEffect, useRef } from 'react';
import './PixelCharacter.css';

interface PixelCharacterProps {
  size?: number;
  animate?: boolean;
  className?: string;
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

function PixelCharacter({ size = 64, animate = true, className }: PixelCharacterProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

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

  return (
    <canvas
      ref={canvasRef}
      className={`pixel-character ${className || ''}`}
      style={{ width: size, height: size, imageRendering: 'pixelated' }}
    />
  );
}

export default PixelCharacter;
