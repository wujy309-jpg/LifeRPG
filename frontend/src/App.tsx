import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ActivityLog from './components/ActivityLog';
import CharacterSheet from './components/CharacterSheet';
import Inventory from './components/Inventory';
import QuestBoard from './components/QuestBoard';
import PixelCharacter from './components/PixelCharacter';
import AISettings from './components/AISettings';
import CharacterManager from './components/CharacterManager';
import { MapIcon, ScrollIcon, ShieldIcon, ChestIcon, QuestIcon } from './components/GameIcons';
import { getCharacterFull, createCharacter } from './services/api';
import type { CharacterFull } from './services/api';
import './App.css';

function App() {
  const [characterId, setCharacterId] = useState<number | null>(() => {
    const saved = localStorage.getItem('liferpg_character_id');
    return saved ? parseInt(saved) : null;
  });
  const [characterData, setCharacterData] = useState<CharacterFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAISettings, setShowAISettings] = useState(false);
  const [showCharacterManager, setShowCharacterManager] = useState(false);

  const loadCharacter = async () => {
    if (!characterId) {
      setLoading(false);
      return;
    }
    try {
      const data = await getCharacterFull(characterId);
      setCharacterData(data);
    } catch (e) {
      console.error('加载角色失败:', e);
      localStorage.removeItem('liferpg_character_id');
      setCharacterId(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCharacter();
  }, [characterId]);

  const handleCharacterCreated = (id: number) => {
    localStorage.setItem('liferpg_character_id', id.toString());
    setCharacterId(id);
    setShowCharacterManager(false);
  };

  const handleCharacterSwitch = (id: number) => {
    localStorage.setItem('liferpg_character_id', id.toString());
    setCharacterId(id);
    setShowCharacterManager(false);
  };

  const handleCharacterDelete = () => {
    localStorage.removeItem('liferpg_character_id');
    setCharacterId(null);
    setCharacterData(null);
    setShowCharacterManager(false);
  };

  const handleRefresh = () => {
    loadCharacter();
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    );
  }

  if (!characterId || !characterData) {
    return <WelcomeScreen onCharacterCreated={handleCharacterCreated} />;
  }

  return (
    <Router>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <h1>LifeRPG</h1>
            <p className="subtitle">生活游戏化</p>
          </div>
          <div className="nav-links">
            <Link to="/" className="nav-link">
              <span className="icon"><MapIcon size={20} /></span>
              仪表盘
            </Link>
            <Link to="/activity" className="nav-link">
              <span className="icon"><ScrollIcon size={20} /></span>
              记录活动
            </Link>
            <Link to="/character" className="nav-link">
              <span className="icon"><ShieldIcon size={20} /></span>
              角色属性
            </Link>
            <Link to="/inventory" className="nav-link">
              <span className="icon"><ChestIcon size={20} /></span>
              装备背包
            </Link>
            <Link to="/quests" className="nav-link">
              <span className="icon"><QuestIcon size={20} /></span>
              任务板
            </Link>
            <button 
              className="nav-link ai-settings-btn"
              onClick={() => setShowAISettings(true)}
            >
              <span className="icon">⚙️</span>
              AI 设置
            </button>
          </div>
          <div className="character-mini">
            <div className="mini-avatar">
              <PixelCharacter size={48} animate={true} />
            </div>
            <div className="mini-info">
              <span className="mini-name">{characterData.character.name}</span>
              <span className="mini-level">Lv.{characterData.character.level} {characterData.level_title}</span>
            </div>
            <button 
              className="switch-character-btn"
              onClick={() => setShowCharacterManager(true)}
              title="切换角色"
            >
              切换
            </button>
          </div>
        </nav>
        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard data={characterData} onRefresh={handleRefresh} />} />
            <Route path="/activity" element={<ActivityLog characterId={characterId} onActivityLogged={handleRefresh} />} />
            <Route path="/character" element={<CharacterSheet data={characterData} />} />
            <Route path="/inventory" element={<Inventory characterId={characterId} />} />
            <Route path="/quests" element={<QuestBoard characterId={characterId} onQuestComplete={handleRefresh} />} />
          </Routes>
        </main>
      </div>
      {showAISettings && (
        <AISettings onClose={() => setShowAISettings(false)} />
      )}
      {showCharacterManager && (
        <CharacterManager
          currentCharacterId={characterId}
          onCharacterSwitch={handleCharacterSwitch}
          onCharacterDelete={handleCharacterDelete}
          onCharacterCreated={handleCharacterCreated}
          onClose={() => setShowCharacterManager(false)}
        />
      )}
    </Router>
  );
}

function WelcomeScreen({ onCharacterCreated }: { onCharacterCreated: (id: number) => void }) {
  const [name, setName] = useState('');
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [education, setEducation] = useState('');
  const [occupation, setOccupation] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const character = await createCharacter(
        name.trim(),
        gender,
        age ? parseInt(age) : 0,
        height ? parseFloat(height) : 0,
        weight ? parseFloat(weight) : 0,
        education,
        occupation
      );
      onCharacterCreated(character.id);
    } catch (e) {
      console.error('创建角色失败:', e);
      alert('创建失败，请确保后端服务正在运行');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h1 className="welcome-title">LifeRPG</h1>
        <p className="welcome-subtitle">把你的生活变成一场冒险</p>
        <div className="welcome-features">
          <div className="feature">
            <span className="feature-icon">⚔️</span>
            <span>记录活动获得经验值</span>
          </div>
          <div className="feature">
            <span className="feature-icon"> </span>
            <span>收集装备提升属性</span>
          </div>
          <div className="feature">
            <span className="feature-icon"> </span>
            <span>解锁趣味称号</span>
          </div>
          <div className="feature">
            <span className="feature-icon"> </span>
            <span>AI生成每日任务</span>
          </div>
        </div>
        
        <div className="create-form">
          <input
            type="text"
            placeholder="输入你的冒险者名称..."
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="name-input"
          />
          
          {!showForm ? (
            <button 
              onClick={() => setShowForm(true)} 
              disabled={!name.trim()} 
              className="create-btn"
            >
              下一步：填写个人信息
            </button>
          ) : (
            <div className="personal-info-form">
              <p className="form-hint">填写个人信息可获得更准确的初始属性</p>
              
              <div className="form-row">
                <div className="form-group">
                  <label>性别</label>
                  <select value={gender} onChange={(e) => setGender(e.target.value)}>
                    <option value="">请选择</option>
                    <option value="男">男</option>
                    <option value="女">女</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>年龄</label>
                  <input
                    type="number"
                    placeholder="如：25"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>身高 (cm)</label>
                  <input
                    type="number"
                    placeholder="如：175"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>体重 (kg)</label>
                  <input
                    type="number"
                    placeholder="如：70"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>学历</label>
                  <select value={education} onChange={(e) => setEducation(e.target.value)}>
                    <option value="">请选择</option>
                    <option value="小学">小学</option>
                    <option value="初中">初中</option>
                    <option value="高中">高中</option>
                    <option value="大专">大专</option>
                    <option value="本科">本科</option>
                    <option value="硕士">硕士</option>
                    <option value="博士">博士</option>
                    <option value="其他">其他</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>职业</label>
                  <select value={occupation} onChange={(e) => setOccupation(e.target.value)}>
                    <option value="">请选择</option>
                    <option value="学生">学生</option>
                    <option value="程序员">程序员</option>
                    <option value="设计师">设计师</option>
                    <option value="教师">教师</option>
                    <option value="医生">医生</option>
                    <option value="律师">律师</option>
                    <option value="销售">销售</option>
                    <option value="工人">工人</option>
                    <option value="运动员">运动员</option>
                    <option value="艺术家">艺术家</option>
                    <option value="自由职业">自由职业</option>
                    <option value="企业管理">企业管理</option>
                    <option value="公务员">公务员</option>
                    <option value="服务业">服务业</option>
                    <option value="其他">其他</option>
                  </select>
                </div>
              </div>
              
              <div className="form-actions">
                <button 
                  onClick={() => setShowForm(false)} 
                  className="back-btn"
                >
                  返回
                </button>
                <button 
                  onClick={handleCreate} 
                  disabled={creating || !name.trim()} 
                  className="create-btn"
                >
                  {creating ? '创建中...' : '开始冒险'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
