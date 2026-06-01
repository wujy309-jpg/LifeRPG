import { useState, useEffect } from 'react';
import { getTemplates, addTemplate, deleteTemplate, useTemplate, logActivity } from '../services/api';
import type { ActivityTemplate } from '../services/api';
import './ActivityTemplates.css';

interface ActivityTemplatesProps {
  characterId: number;
  onActivityLogged: () => void;
}

function ActivityTemplates({ characterId, onActivityLogged }: ActivityTemplatesProps) {
  const [templates, setTemplates] = useState<ActivityTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newType, setNewType] = useState('');
  const [using, setUsing] = useState<number | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [characterId]);

  const loadTemplates = async () => {
    try {
      const data = await getTemplates(characterId);
      setTemplates(data);
    } catch (e) {
      console.error('加载模板失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newName.trim() || !newDesc.trim()) {
      alert('请填写名称和描述');
      return;
    }
    try {
      await addTemplate(characterId, newName, newDesc, newType || undefined);
      setNewName('');
      setNewDesc('');
      setNewType('');
      setShowAdd(false);
      await loadTemplates();
    } catch (e) {
      console.error('添加模板失败:', e);
      alert('添加失败');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定删除这个模板？')) return;
    try {
      await deleteTemplate(id);
      await loadTemplates();
    } catch (e) {
      console.error('删除模板失败:', e);
    }
  };

  const handleUse = async (template: ActivityTemplate) => {
    setUsing(template.id);
    try {
      // 增加使用次数
      await useTemplate(template.id);
      // 记录活动
      await logActivity(characterId, template.description);
      await loadTemplates();
      onActivityLogged();
    } catch (e) {
      console.error('使用模板失败:', e);
      alert('记录失败，请重试');
    } finally {
      setUsing(null);
    }
  };

  const activityTypes = [
    { value: '学习', label: '  学习' },
    { value: '运动', label: '  运动' },
    { value: '编程', label: '  编程' },
    { value: '社交', label: '  社交' },
    { value: '工作', label: '  工作' },
    { value: '创作', label: '  创作' },
    { value: '生活', label: '  生活' },
    { value: '休息', label: '  休息' },
  ];

  if (loading) {
    return <div className="templates-loading">加载中...</div>;
  }

  return (
    <div className="templates-container">
      <div className="templates-header">
        <h3>  活动模板</h3>
        <button className="add-btn" onClick={() => setShowAdd(!showAdd)}>
          {showAdd ? '取消' : '+ 添加模板'}
        </button>
      </div>

      {/* 添加模板表单 */}
      {showAdd && (
        <div className="add-form">
          <input
            type="text"
            placeholder="模板名称（如：晨跑）"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="form-input"
          />
          <input
            type="text"
            placeholder="活动描述（如：跑步30分钟）"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="form-input"
          />
          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            className="form-select"
          >
            <option value="">自动识别类型</option>
            {activityTypes.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button className="submit-btn" onClick={handleAdd}>保存模板</button>
        </div>
      )}

      {/* 模板列表 */}
      {templates.length > 0 ? (
        <div className="templates-list">
          {templates.map(template => (
            <div key={template.id} className="template-card">
              <div className="template-info">
                <div className="template-header">
                  <span className="template-name">{template.name}</span>
                  {template.activity_type && (
                    <span className="template-type">{template.activity_type}</span>
                  )}
                </div>
                <p className="template-desc">{template.description}</p>
                <span className="template-count">使用 {template.use_count} 次</span>
              </div>
              <div className="template-actions">
                <button
                  className="use-btn"
                  onClick={() => handleUse(template)}
                  disabled={using === template.id}
                >
                  {using === template.id ? '记录中...' : '  使用'}
                </button>
                <button
                  className="delete-btn"
                  onClick={() => handleDelete(template.id)}
                >
                   ️
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>还没有活动模板</p>
          <p className="hint">添加常用活动，一键记录更方便！</p>
        </div>
      )}

      {/* 使用说明 */}
      <div className="templates-guide">
        <p>  <strong>小贴士：</strong>添加常用的活动模板，下次记录时直接点击使用，省去输入的麻烦！</p>
      </div>
    </div>
  );
}

export default ActivityTemplates;
