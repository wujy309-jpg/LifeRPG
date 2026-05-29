import type { CharacterFull } from '../services/api';
import RadarChart from './RadarChart';
import './CharacterSheet.css';

interface CharacterSheetProps {
  data: CharacterFull;
}

function CharacterSheet({ data }: CharacterSheetProps) {
  const { character, level_title, next_level_exp, titles } = data;

  const stats = [
    { name: '力量', value: character.strength, icon: ' ', color: '#ff6b6b', desc: '身体素质、运动能力' },
    { name: '智力', value: character.intelligence, icon: ' ', color: '#4ecdc4', desc: '学习能力、逻辑思维' },
    { name: '敏捷', value: character.agility, icon: ' ', color: '#45b7d1', desc: '反应速度、灵活性' },
    { name: '魅力', value: character.charisma, icon: ' ', color: '#f9ca24', desc: '社交能力、领导力' },
    { name: '意志', value: character.willpower, icon: ' ️', color: '#a55eea', desc: '毅力、自控力' },
  ];

  const totalStats = stats.reduce((sum, s) => sum + s.value, 0);
  const maxStat = Math.max(...stats.map(s => s.value));

  const expPercentage = (character.exp / next_level_exp) * 100;

  return (
    <div className="character-page">
      <header className="page-header">
        <h2> ️ 角色属性</h2>
      </header>

      {/* 角色信息卡 */}
      <div className="character-card">
        <div className="card-left">
          <div className="large-avatar">
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
                  <span className="stat-icon">{stat.icon}</span>
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
