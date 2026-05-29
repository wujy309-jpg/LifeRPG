import type { CSSProperties } from 'react';

// RPG 图标映射
// 使用 Iconify API 获取游戏风格图标

interface GameIconProps {
  icon: string;
  size?: number;
  color?: string;
  className?: string;
  style?: CSSProperties;
}

// 图标映射表 - 使用 game-icons 和 mdi 图标集
export const ICONS = {
  // 属性图标
  strength: 'game-icons:muscle-up',
  intelligence: 'game-icons:brain',
  agility: 'game-icons:running-shoe',
  charisma: 'game-icons:charisma',
  willpower: 'game-icons:willpower',
  
  // 功能图标
  dashboard: 'game-icons:castle',
  activity: 'game-icons:scroll-unfurled',
  character: 'game-icons:character',
  inventory: 'game-icons:knapsack',
  quest: 'game-icons:quest',
  scroll: 'game-icons:scroll-unfurled',
  chest: 'game-icons:chest-armor',
  crown: 'game-icons:crown',
  
  // 资源图标
  exp: 'game-icons:sparkles',
  gold: 'game-icons:coins',
  level: 'game-icons:upgrade',
  hp: 'game-icons:health-potion',
  mp: 'game-icons:potion-ball',
  
  // 装备图标
  sword: 'game-icons:sword-brandish',
  shield: 'game-icons:shield',
  helmet: 'game-icons:helmet',
  armor: 'game-icons:chest-armor',
  boots: 'game-icons:boots',
  ring: 'game-icons:ring',
  amulet: 'game-icons:amulet',
  
  // 活动图标
  study: 'game-icons:book-cover',
  exercise: 'game-icons:lifting',
  coding: 'game-icons:computer',
  social: 'game-icons:conversation',
  work: 'game-icons:briefcase',
  create: 'game-icons:paint-brush',
  lifestyle: 'game-icons:house',
  rest: 'game-icons:sleeping',
  
  // 任务图标
  daily: 'game-icons:sundial',
  weekly: 'game-icons:calendar',
  achievement: 'game-icons:trophy',
  
  // 稀有度图标
  common: 'game-icons:plain-circle',
  rare: 'game-icons:large-diamond',
  epic: 'game-icons:star-swirl',
  legendary: 'game-icons:crown',
  
  // 其他
  settings: 'game-icons:gears',
  help: 'game-icons:question-mark',
  close: 'game-icons:cancel',
  check: 'game-icons:check-mark',
  arrow: 'game-icons:arrow-right',
};

// 稀有度颜色
export const RARITY_COLORS: Record<string, string> = {
  '普通': '#9d9d9d',
  '稀有': '#0070dd',
  '史诗': '#a335ee',
  '传说': '#ff8000',
};

// 属性颜色
export const STAT_COLORS: Record<string, string> = {
  strength: '#ff6b6b',
  intelligence: '#4ecdc4',
  agility: '#45b7d1',
  charisma: '#f9ca24',
  willpower: '#a55eea',
};

// 图标组件
export function GameIcon({ icon, size = 24, color, className, style }: GameIconProps) {
  return (
    <span
      className={`game-icon ${className || ''}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: size,
        height: size,
        ...style,
      }}
    >
      <img
        src={`https://api.iconify.design/${icon}.svg?width=${size}&height=${size}&color=${encodeURIComponent(color || 'currentColor')}`}
        width={size}
        height={size}
        alt=""
        style={{ filter: color ? 'none' : 'brightness(0) invert(1)' }}
      />
    </span>
  );
}

// 获取属性图标
export function getStatIcon(stat: string): string {
  return ICONS[stat as keyof typeof ICONS] || ICONS.strength;
}

// 获取活动图标
export function getActivityIcon(activity: string): string {
  const activityMap: Record<string, string> = {
    '学习': ICONS.study,
    '运动': ICONS.exercise,
    '编程': ICONS.coding,
    '社交': ICONS.social,
    '工作': ICONS.work,
    '创作': ICONS.create,
    '生活': ICONS.lifestyle,
    '休息': ICONS.rest,
  };
  return activityMap[activity] || ICONS.activity;
}

// 获取稀有度图标
export function getRarityIcon(rarity: string): string {
  return ICONS[rarity as keyof typeof ICONS] || ICONS.common;
}

export default GameIcon;
