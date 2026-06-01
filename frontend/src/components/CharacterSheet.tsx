import type { CharacterFull } from '../services/api';
import RadarChart from './RadarChart';
import { StrengthIcon, IntelligenceIcon, AgilityIcon, CharismaIcon, WillpowerIcon } from './GameIcons';
import './CharacterSheet.css';

interface CharacterSheetProps {
  data: CharacterFull;
}

// 根据总属性获取边框颜色
function getAvatarFrameStyle(score: number) {
  if (score >= 90) {
    return { borderColor: '#ef4444', glowColor: 'rgba(239,68,68,0.6)', className: 'frame-red' };
  } else if (score >= 80) {
    return { borderColor: '#f59e0b', glowColor: 'rgba(245,158,11,0.5)', className: 'frame-gold' };
  } else if (score >= 70) {
    return { borderColor: '#a855f7', glowColor: 'rgba(168,85,247,0.4)', className: 'frame-purple' };
  } else if (score >= 60) {
    return { borderColor: '#3b82f6', glowColor: 'rgba(59,130,246,0.4)', className: 'frame-blue' };
  } else if (score >= 50) {
    return { borderColor: '#22c55e', glowColor: 'rgba(34,197,94,0.3)', className: 'frame-green' };
  } else if (score >= 40) {
    return { borderColor: '#ffffff', glowColor: 'rgba(255,255,255,0.3)', className: 'frame-white' };
  }
  return { borderColor: 'var(--border-dark)', glowColor: 'transparent', className: '' };
}

function CharacterSheet({ data }: CharacterSheetProps) {
  const { character, level_title, next_level_exp, titles } = data;

  const stats = [
    { name: '力量', value: character.strength, icon: 'strength', color: '#ef4444', desc: '身体素质、运动能力' },
    { name: '智力', value: character.intelligence, icon: 'intelligence', color: '#3b82f6', desc: '学习能力、逻辑思维' },
    { name: '敏捷', value: character.agility, icon: 'agility', color: '#22c55e', desc: '反应速度、灵活性' },
    { name: '魅力', value: character.charisma, icon: 'charisma', color: '#a855f7', desc: '社交能力、领导力' },
    { name: '意志', value: character.willpower, icon: 'willpower', color: '#f59e0b', desc: '毅力、自控力' },
  ];

  const renderStatIcon = (iconName: string, color: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      strength: <StrengthIcon size={20} />,
      intelligence: <IntelligenceIcon size={20} />,
      agility: <AgilityIcon size={20} />,
      charisma: <CharismaIcon size={20} />,
      willpower: <WillpowerIcon size={20} />,
    };
    return <span className="stat-icon" style={{ color }}>{iconMap[iconName] || null}</span>;
  };

  const totalStats = Math.round(stats.reduce((sum, s) => sum + s.value, 0) / 5);
  const maxStat = Math.max(...stats.map(s => s.value));
  const frameStyle = getAvatarFrameStyle(totalStats);

  const expPercentage = (character.exp / next_level_exp) * 100;

  return (
    <div className="character-page">
      <header className="page-header">
        <h2> ️ 角色属性</h2>
      </header>

      {/* 角色信息卡 */}
      <div className="character-card">
        <div className="card-left">
          <div 
            className={`large-avatar ${frameStyle.className}`}
            style={{
              borderColor: frameStyle.borderColor,
              boxShadow: `0 0 15px ${frameStyle.glowColor}, 0 0 30px ${frameStyle.glowColor}`
            }}
          >
            {character.name.charAt(0)}
          </div>
          <div className="name-section">
            <h3 className="char-name">{character.name}</h3>
            <span className="char-title">{level_title}</span>
          </div>
        </div>
        <div className="card-right">
          <div className="level-info">
            <span className="level-badge">Lv.{character.level}</span>
            <div className="exp-bar-wrapper">
              <div className="exp-bar-bg">
                <div className="exp-bar-fill" style={{ width: `${expPercentage}%` }}></div>
              </div>
              <span className="exp-text">{character.exp} / {next_level_exp} EXP</span>
            </div>
          </div>
          <div className="gold-display">
            <span className="gold-icon"> </span>
            <span className="gold-amount">{character.gold}</span>
          </div>
        </div>
      </div>

      {/* 属性详情 */}
      <div className="stats-section">
        <h3>属性面板 <span className="total-stats">总属性: {totalStats}</span></h3>
        <div className="stats-content">
          <div className="radar-wrapper">
            <RadarChart
              stats={{
                strength: character.strength,
                intelligence: character.intelligence,
                agility: character.agility,
                charisma: character.charisma,
                willpower: character.willpower
              }}
              size={240}
              animated={true}
            />
          </div>
          <div className="stats-list">
            {stats.map(stat => (
              <div key={stat.name} className="stat-row">
                <div className="stat-header">
                  {renderStatIcon(stat.icon, stat.color)}
                  <span className="stat-name">{stat.name}</span>
                  <span className="stat-value" style={{ color: stat.color }}>{stat.value}</span>
                </div>
                <div className="stat-bar-bg">
                  <div
                    className="stat-bar-fill"
                    style={{
                      width: `${(stat.value / maxStat) * 100}%`,
                      backgroundColor: stat.color
                    }}
                  ></div>
                </div>
                <span className="stat-desc">{stat.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 称号列表 */}
      <div className="titles-section">
        <h3>  称号收藏 <span className="count">({titles.length})</span></h3>
        {titles.length > 0 ? (
          <div className="titles-grid">
            {titles.map(title => (
              <div key={title.id} className={`title-card ${title.equipped ? 'equipped' : ''}`}>
                <div className="title-header">
                  <span className="title-name">「{title.name}」</span>
                  {title.equipped && <span className="equipped-badge">已装备</span>}
                </div>
                <p className="title-desc">{title.description}</p>
                {title.unlock_condition && (
                  <p className="unlock-condition">解锁条件: {title.unlock_condition}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>还没有获得任何称号</p>
            <p className="hint">记录活动来解锁称号吧！</p>
          </div>
        )}
      </div>

      {/* 等级头衔说明 */}
      <div className="level-titles-section">
        <h3>  等级头衔</h3>
        <div className="level-titles-list">
          <div className={`level-title-item ${character.level >= 1 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.1-4</span>
            <span className="title-name">新手冒险者</span>
            {character.level >= 1 && <span className="check">✓</span>}
          </div>
          <div className={`level-title-item ${character.level >= 5 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.5-9</span>
            <span className="title-name">初级勇者</span>
            {character.level >= 5 && <span className="check">✓</span>}
          </div>
          <div className={`level-title-item ${character.level >= 10 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.10-19</span>
            <span className="title-name">中级战士</span>
            {character.level >= 10 && <span className="check">✓</span>}
          </div>
          <div className={`level-title-item ${character.level >= 20 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.20-29</span>
            <span className="title-name">高级英雄</span>
            {character.level >= 20 && <span className="check">✓</span>}
          </div>
          <div className={`level-title-item ${character.level >= 30 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.30-49</span>
            <span className="title-name">传奇大师</span>
            {character.level >= 30 && <span className="check">✓</span>}
          </div>
          <div className={`level-title-item ${character.level >= 50 ? 'unlocked' : ''}`}>
            <span className="level-range">Lv.50+</span>
            <span className="title-name">不朽传说</span>
            {character.level >= 50 && <span className="check">✓</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CharacterSheet;
