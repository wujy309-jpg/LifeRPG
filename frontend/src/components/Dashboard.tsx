import { useState, useCallback } from 'react';
import { logActivity } from '../services/api';
import type { CharacterFull, GameFeedback } from '../services/api';
import RadarChart from './RadarChart';
import LevelUpEffect from './LevelUpEffect';
import StatChangeEffect from './StatChangeEffect';
import DailyCheckIn from './DailyCheckIn';
import { GameIcon, ICONS, STAT_COLORS } from './GameIcons';
import PixelCharacter from './PixelCharacter';
import './Dashboard.css';
import './GameIcons.css';

interface DashboardProps {
  data: CharacterFull;
  onRefresh: () => void;
}

function Dashboard({ data, onRefresh }: DashboardProps) {
  const [quickInput, setQuickInput] = useState('');
  const [feedback, setFeedback] = useState<GameFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [showLevelUp, setShowLevelUp] = useState(false);
  const [showStatChange, setShowStatChange] = useState(false);
  const [statChanges, setStatChanges] = useState<Record<string, number>>({});

  const { character, equipment, titles, active_quests, recent_activities, next_level_exp, level_title } = data;

  const expPercentage = (character.exp / next_level_exp) * 100;
  
  // 计算总属性(平均值，范围0-100)
  const totalScore = Math.round(
    (character.strength + character.intelligence + character.agility + character.charisma + character.willpower) / 5
  );

  const handleStatChangeComplete = useCallback(() => {
    setShowStatChange(false);
    setStatChanges({});
  }, []);

  const handleQuickLog = async () => {
    if (!quickInput.trim()) return;
    setSubmitting(true);
    try {
      const result = await logActivity(character.id, quickInput);
      setFeedback(result);
      setShowFeedback(true);
      setQuickInput('');
      
      // 检查是否有属性变化
      if (result.activity_log.attribute_changes) {
        const changes = JSON.parse(result.activity_log.attribute_changes);
        if (Object.keys(changes).length > 0) {
          setStatChanges(changes);
          setShowStatChange(true);
        }
      }
      
      // 检查是否升级
      if (result.level_up) {
        setTimeout(() => {
          setShowLevelUp(true);
        }, 1000);
      }
      
      onRefresh();
    } catch (e) {
      console.error('记录失败:', e);
      alert('记录失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  const getRarityColor = (rarity: string) => {
    const colors: Record<string, string> = {
      '普通': '#9d9d9d',
      '稀有': '#0070dd',
      '史诗': '#a335ee',
      '传说': '#ff8000'
    };
    return colors[rarity] || '#9d9d9d';
  };

  const formatActivityTime = (createdAt: string) => {
    const date = new Date(createdAt);
    const now = new Date();
    
    const isToday = date.toDateString() === now.toDateString();
    
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();
    
    const timeStr = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    if (isToday) {
      return timeStr;
    } else if (isYesterday) {
      return `昨天 ${timeStr}`;
    } else {
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${month}-${day} ${timeStr}`;
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h2>
          <GameIcon icon={ICONS.dashboard} size={24} style={{ marginRight: 10 }} />
          冒险者仪表盘
        </h2>
        <div className="header-stats">
          <span className="stat gold">
            <GameIcon icon={ICONS.gold} size={18} />
            {character.gold}
          </span>
          <span className="stat level">
            <GameIcon icon={ICONS.level} size={18} />
            Lv.{character.level}
          </span>
        </div>
      </header>

      {/* 角色概览卡片 */}
      <div className="character-overview">
        <div className="avatar-section">
          <div className="pixel-avatar-wrapper">
            <PixelCharacter size={72} animate={true} score={totalScore} />
          </div>
          <div className="character-title">
            <h3>{character.name}</h3>
            <span className="title-badge">{level_title}</span>
          </div>
        </div>
        <div className="exp-section">
          <div className="exp-bar-container">
            <div className="exp-bar" style={{ width: `${expPercentage}%` }}></div>
          </div>
          <span className="exp-text">EXP: {character.exp} / {next_level_exp}</span>
        </div>
      </div>

      {/* 每日签到 */}
      <DailyCheckIn characterId={character.id} onCheckIn={onRefresh} />

      {/* 属性雷达图 */}
      <div className="radar-section">
        <div className="radar-wrapper">
          <RadarChart
            stats={{
              strength: character.strength,
              intelligence: character.intelligence,
              agility: character.agility,
              charisma: character.charisma,
              willpower: character.willpower
            }}
            size={280}
            animated={true}
          />
        </div>
        <div className="stats-legend">
          <div className="legend-item">
            <GameIcon icon={ICONS.strength} size={22} color={STAT_COLORS.strength} />
            <span className="legend-label">力量</span>
            <span className="legend-value">{character.strength}</span>
          </div>
          <div className="legend-item">
            <GameIcon icon={ICONS.intelligence} size={22} color={STAT_COLORS.intelligence} />
            <span className="legend-label">智力</span>
            <span className="legend-value">{character.intelligence}</span>
          </div>
          <div className="legend-item">
            <GameIcon icon={ICONS.agility} size={22} color={STAT_COLORS.agility} />
            <span className="legend-label">敏捷</span>
            <span className="legend-value">{character.agility}</span>
          </div>
          <div className="legend-item">
            <GameIcon icon={ICONS.charisma} size={22} color={STAT_COLORS.charisma} />
            <span className="legend-label">魅力</span>
            <span className="legend-value">{character.charisma}</span>
          </div>
          <div className="legend-item">
            <GameIcon icon={ICONS.willpower} size={22} color={STAT_COLORS.willpower} />
            <span className="legend-label">意志</span>
            <span className="legend-value">{character.willpower}</span>
          </div>
        </div>
      </div>

      {/* 快速记录 */}
      <div className="quick-log">
        <h3>
          <GameIcon icon={ICONS.scroll} size={20} style={{ marginRight: 8 }} />
          快速记录
        </h3>
        <div className="quick-input-row">
          <input
            type="text"
            placeholder="告诉我你今天做了什么...（如：去上课、健身、写代码）"
            value={quickInput}
            onChange={(e) => setQuickInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleQuickLog()}
            disabled={submitting}
          />
          <button onClick={handleQuickLog} disabled={submitting || !quickInput.trim()}>
            {submitting ? '记录中...' : '记录'}
          </button>
        </div>
        <div className="quick-tags">
          <button className="tag" onClick={() => setQuickInput('去上课了')}>
            <GameIcon icon={ICONS.study} size={16} /> 上课
          </button>
          <button className="tag" onClick={() => setQuickInput('去健身房锻炼了1小时')}>
            <GameIcon icon={ICONS.exercise} size={16} /> 健身
          </button>
          <button className="tag" onClick={() => setQuickInput('写了一下午代码')}>
            <GameIcon icon={ICONS.coding} size={16} /> 写代码
          </button>
          <button className="tag" onClick={() => setQuickInput('和朋友聚餐')}>
            <GameIcon icon={ICONS.social} size={16} /> 社交
          </button>
          <button className="tag" onClick={() => setQuickInput('看了一本书')}>
            <GameIcon icon={ICONS.study} size={16} /> 看书
          </button>
          <button className="tag" onClick={() => setQuickInput('打扫了房间')}>
            <GameIcon icon={ICONS.lifestyle} size={16} /> 打扫
          </button>
        </div>
      </div>

      {/* 反馈弹窗 */}
      {showFeedback && feedback && (
        <div className="feedback-overlay" onClick={() => setShowFeedback(false)}>
          <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setShowFeedback(false)}>×</button>
            <h2 className="feedback-title">活动记录成功！</h2>

            <div className="feedback-gains">
              <div className="gain exp">
                <GameIcon icon={ICONS.exp} size={28} style={{ marginBottom: 8 }} />
                <span className="gain-label">经验值</span>
                <span className="gain-value">+{feedback.activity_log.exp_gained}</span>
              </div>
              <div className="gain gold">
                <GameIcon icon={ICONS.gold} size={28} style={{ marginBottom: 8 }} />
                <span className="gain-label">金币</span>
                <span className="gain-value">+{feedback.activity_log.gold_gained}</span>
              </div>
            </div>

            {feedback.level_up && (
              <div className="level-up-banner">
                <span className="level-up-icon"> </span>
                <span>恭喜升级！达到 Lv.{feedback.new_level}</span>
              </div>
            )}

            {feedback.equipment_found && (
              <div className="equipment-found" style={{ borderColor: getRarityColor(feedback.equipment_found.rarity) }}>
                <h4>获得装备</h4>
                <p className="equip-name" style={{ color: getRarityColor(feedback.equipment_found.rarity) }}>
                  [{feedback.equipment_found.rarity}] {feedback.equipment_found.name}
                </p>
                <p className="equip-desc">{feedback.equipment_found.description}</p>
              </div>
            )}

            {feedback.title_earned && (
              <div className="title-earned">
                <h4>获得称号</h4>
                <p className="title-name">「{feedback.title_earned.name}」</p>
                <p className="title-desc">{feedback.title_earned.description}</p>
              </div>
            )}

            {feedback.ai_comment && (
              <div className="ai-comment">
                <p className="comment-label">  AI 锐评</p>
                <p className="comment-text">{feedback.ai_comment}</p>
              </div>
            )}

            <button className="confirm-btn" onClick={() => setShowFeedback(false)}>
              继续冒险
            </button>
          </div>
        </div>
      )}

      {/* 底部区域 */}
      <div className="bottom-sections">
        {/* 活跃任务 */}
        <div className="active-quests">
          <h3>
            <GameIcon icon={ICONS.quest} size={18} style={{ marginRight: 8 }} />
            活跃任务
          </h3>
          {active_quests.length > 0 ? (
            <div className="quest-list">
              {active_quests.slice(0, 3).map(quest => (
                <div key={quest.id} className="quest-item">
                  <div className="quest-info">
                    <span className="quest-title">{quest.title}</span>
                    <span className="quest-desc">{quest.description}</span>
                  </div>
                  <div className="quest-rewards">
                    <span className="reward exp">+{quest.exp_reward} EXP</span>
                    <span className="reward gold">+{quest.gold_reward}G</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-text">暂无活跃任务</p>
          )}
        </div>

        {/* 最近活动 */}
        <div className="recent-activities">
          <h3>
            <GameIcon icon={ICONS.activity} size={18} style={{ marginRight: 8 }} />
            最近活动
          </h3>
          {recent_activities.length > 0 ? (
            <div className="activity-list">
              {recent_activities.slice(0, 5).map(log => (
                <div key={log.id} className="activity-item">
                  <span className="activity-type">{log.activity_type}</span>
                  <span className="activity-desc">{log.description}</span>
                  <span className="activity-time">
                    {formatActivityTime(log.created_at)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-text">暂无活动记录</p>
          )}
        </div>

        {/* 装备和称号预览 */}
        <div className="collections-preview">
          <div className="equipment-preview">
            <h3>
              <GameIcon icon={ICONS.chest} size={18} style={{ marginRight: 8 }} />
              最新装备
            </h3>
            {equipment.length > 0 ? (
              <div className="equip-item" style={{ borderColor: getRarityColor(equipment[0].rarity) }}>
                <span className="equip-rarity" style={{ color: getRarityColor(equipment[0].rarity) }}>
                  [{equipment[0].rarity}]
                </span>
                <span className="equip-name">{equipment[0].name}</span>
              </div>
            ) : (
              <p className="empty-text">暂无装备</p>
            )}
          </div>
          <div className="titles-preview">
            <h3>
              <GameIcon icon={ICONS.crown} size={18} style={{ marginRight: 8 }} />
              最新称号
            </h3>
            {titles.length > 0 ? (
              <div className="title-item">
                <span className="title-name">「{titles[0].name}」</span>
              </div>
            ) : (
              <p className="empty-text">暂无称号</p>
            )}
          </div>
        </div>
      </div>

      {/* 升级特效 */}
      <LevelUpEffect
        show={showLevelUp}
        newLevel={feedback?.new_level || character.level}
        onClose={() => setShowLevelUp(false)}
      />

      {/* 属性变化特效 */}
      {showStatChange && (
        <StatChangeEffect
          changes={statChanges}
          stats={{
            strength: { name: '力量', icon: ' ', value: character.strength },
            intelligence: { name: '智力', icon: ' ', value: character.intelligence },
            agility: { name: '敏捷', icon: ' ', value: character.agility },
            charisma: { name: '魅力', icon: ' ', value: character.charisma },
            willpower: { name: '意志', icon: ' ️', value: character.willpower },
          }}
          onComplete={handleStatChangeComplete}
        />
      )}
    </div>
  );
}

export default Dashboard;
