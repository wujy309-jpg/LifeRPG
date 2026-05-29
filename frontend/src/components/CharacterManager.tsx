import { useState, useEffect } from 'react';
import { getAllCharacters, deleteCharacter, createCharacter } from '../services/api';
import type { Character } from '../services/api';
import './CharacterManager.css';

interface CharacterManagerProps {
  currentCharacterId: number;
  onCharacterSwitch: (id: number) => void;
  onCharacterDelete: () => void;
  onCharacterCreated: (id: number) => void;
  onClose: () => void;
}

export default function CharacterManager({ 
  currentCharacterId, 
  onCharacterSwitch, 
  onCharacterDelete,
  onCharacterCreated,
  onClose 
}: CharacterManagerProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  
  // 创建角色表单
  const [name, setName] = useState('');
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [education, setEducation] = useState('');
  const [occupation, setOccupation] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    try {
      setLoading(true);
      const data = await getAllCharacters();
      setCharacters(data.characters);
    } catch (e) {
      console.error('加载角色列表失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (characterId: number) => {
    try {
      await deleteCharacter(characterId);
      if (characterId === currentCharacterId) {
        onCharacterDelete();
      } else {
        loadCharacters();
      }
    } catch (e) {
      console.error('删除角色失败:', e);
      alert('删除失败');
    }
  };

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
    } catch (e: any) {
      console.error('创建角色失败:', e);
      alert(e.response?.data?.detail || '创建失败');
    } finally {
      setCreating(false);
    }
  };

  const getLevelTitle = (level: number) => {
    if (level >= 50) return '不朽传说';
    if (level >= 30) return '传奇大师';
    if (level >= 20) return '高级英雄';
    if (level >= 10) return '中级战士';
    if (level >= 5) return '初级勇者';
    return '新手冒险者';
  };

  const getCharacterStats = (char: Character) => {
    return char.strength + char.intelligence + char.agility + char.charisma + char.willpower;
  };

  return (
    <div className="character-manager-overlay">
      <div className="character-manager-modal">
        <div className="modal-header">
          <h2>⚔️ 角色管理</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : showCreateForm ? (
            <div className="create-character-form">
              <h3>创建新角色</h3>
              <p className="form-hint">填写个人信息可获得更准确的初始属性</p>
              
              <div className="form-group">
                <label>角色名称 *</label>
                <input
                  type="text"
                  placeholder="输入冒险者名称..."
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              
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
                  className="back-btn"
                  onClick={() => setShowCreateForm(false)}
                >
                  返回
                </button>
                <button 
                  className="create-btn"
                  onClick={handleCreate}
                  disabled={creating || !name.trim()}
                >
                  {creating ? '创建中...' : '创建角色'}
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="characters-list">
                {characters.map(char => (
                  <div 
                    key={char.id} 
                    className={`character-card ${char.id === currentCharacterId ? 'active' : ''}`}
                  >
                    <div className="character-info">
                      <div className="character-header">
                        <h3>{char.name}</h3>
                        {char.id === currentCharacterId && (
                          <span className="current-badge">当前</span>
                        )}
                      </div>
                      <div className="character-stats">
                        <span className="level">Lv.{char.level} {getLevelTitle(char.level)}</span>
                        <span className="total-stats">总属性: {getCharacterStats(char)}</span>
                      </div>
                      <div className="character-details">
                        {char.age && char.age > 0 && <span>{char.age}岁</span>}
                        {char.occupation && <span>{char.occupation}</span>}
                      </div>
                    </div>
                    <div className="character-actions">
                      {char.id !== currentCharacterId && (
                        <button 
                          className="switch-btn"
                          onClick={() => onCharacterSwitch(char.id)}
                        >
                          切换
                        </button>
                      )}
                      {deleteConfirm === char.id ? (
                        <div className="delete-confirm">
                          <span>确定删除？</span>
                          <button 
                            className="confirm-yes"
                            onClick={() => handleDelete(char.id)}
                          >
                            是
                          </button>
                          <button 
                            className="confirm-no"
                            onClick={() => setDeleteConfirm(null)}
                          >
                            否
                          </button>
                        </div>
                      ) : (
                        <button 
                          className="delete-btn"
                          onClick={() => setDeleteConfirm(char.id)}
                        >
                          删除
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {characters.length < 3 && (
                <button 
                  className="add-character-btn"
                  onClick={() => setShowCreateForm(true)}
                >
                  + 创建新角色 ({characters.length}/3)
                </button>
              )}
              
              {characters.length >= 3 && (
                <p className="max-characters-hint">
                  已达到最大角色数量（3个），请删除一个角色后再创建新角色
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}