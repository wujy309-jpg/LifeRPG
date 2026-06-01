import { useState } from 'react';
import { exportData } from '../services/api';
import './DataExport.css';

interface DataExportProps {
  characterId: number;
  characterName: string;
}

function DataExport({ characterId, characterName }: DataExportProps) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(true);
    setError(null);
    try {
      const data = await exportData(characterId, format);
      
      // 创建下载文件
      let content: string;
      let filename: string;
      let mimeType: string;
      
      if (format === 'csv') {
        content = data.data;
        filename = `${characterName}_活动记录_${new Date().toISOString().split('T')[0]}.csv`;
        mimeType = 'text/csv;charset=utf-8;';
      } else {
        content = JSON.stringify(data, null, 2);
        filename = `${characterName}_完整数据_${new Date().toISOString().split('T')[0]}.json`;
        mimeType = 'application/json;charset=utf-8;';
      }
      
      // 添加BOM头以支持中文
      const bom = format === 'csv' ? '\uFEFF' : '';
      const blob = new Blob([bom + content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      
      // 触发下载
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error('导出失败:', e);
      setError('导出失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-container">
      <h3>  数据导出</h3>
      <p className="export-desc">导出你的游戏数据，用于备份或分析</p>
      
      {error && <div className="export-error">{error}</div>}
      
      <div className="export-options">
        <div className="export-card">
          <div className="export-icon"> </div>
          <h4>JSON 格式</h4>
          <p>导出完整数据，包括角色信息、活动记录、装备、称号、任务等</p>
          <p className="export-hint">适合备份和恢复</p>
          <button 
            className="export-btn json"
            onClick={() => handleExport('json')}
            disabled={exporting}
          >
            {exporting ? '导出中...' : '导出 JSON'}
          </button>
        </div>
        
        <div className="export-card">
          <div className="export-icon"> </div>
          <h4>CSV 格式</h4>
          <p>只导出活动记录，可以用 Excel 打开</p>
          <p className="export-hint">适合数据分析</p>
          <button 
            className="export-btn csv"
            onClick={() => handleExport('csv')}
            disabled={exporting}
          >
            {exporting ? '导出中...' : '导出 CSV'}
          </button>
        </div>
      </div>
      
      <div className="export-note">
        <p>  <strong>提示：</strong>建议定期导出数据作为备份，防止数据丢失。</p>
      </div>
    </div>
  );
}

export default DataExport;
