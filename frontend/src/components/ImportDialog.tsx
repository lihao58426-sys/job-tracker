import { useState } from 'react';
import { importBatch } from '../api';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ImportDialog({ open, onClose, onSuccess }: Props) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ created: number; skipped: number; duplicates: number; errors: string[] } | null>(null);
  const [error, setError] = useState('');

  if (!open) return null;

  async function handleImport() {
    setError('');
    setResult(null);
    try {
      const jobs = JSON.parse(text);
      const arr = Array.isArray(jobs) ? jobs : (jobs.data || []);
      if (arr.length === 0) {
        setError('未找到有效的岗位数据。请粘贴 JSON 数组。');
        return;
      }
      setLoading(true);
      const res = await importBatch(arr);
      setResult(res);
      if (res.created > 0) onSuccess();
    } catch (e) {
      setError(`JSON 解析失败：${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24, width: 680, maxHeight: '85vh',
        display: 'flex', flexDirection: 'column', boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
      }}>
        <h3 style={{ marginBottom: 16 }}>📥 批量导入岗位</h3>

        <p style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
          粘贴 scored_batch.json 格式的 JSON 数组，或爬虫结果中的 data 数组。
        </p>

        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder='[{"title": "AI Agent工程师", "company": "XX科技", "salary": "15-30k", ...}]'
          rows={14}
          style={{
            width: '100%', padding: 12, borderRadius: 8, border: '1px solid #d9d9d9',
            fontFamily: 'monospace', fontSize: 12, resize: 'vertical',
          }}
        />

        {error && <p style={{ color: '#f5222d', fontSize: 13, marginTop: 8 }}>{error}</p>}

        {result && (
          <div style={{
            marginTop: 12, padding: 12, background: '#f6ffed', borderRadius: 8, fontSize: 13,
          }}>
            <p style={{ color: '#52c41a', fontWeight: 600 }}>
              成功导入 {result.created} 条
            </p>
            {(result.duplicates > 0 || result.skipped > 0) && (
              <p style={{ color: '#faad14', marginTop: 4 }}>
                {result.duplicates > 0 && `去重跳过 ${result.duplicates} 条  `}
                {result.skipped > 0 && `其他跳过 ${result.skipped} 条`}
              </p>
            )}
            {result.errors.length > 0 && (
              <div style={{ color: '#f5222d', marginTop: 6, maxHeight: 120, overflow: 'auto' }}>
                {result.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, marginTop: 16, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={btnStyle('#d9d9d9', '#333')}>
            取消
          </button>
          <button onClick={handleImport} disabled={loading || !text.trim()} style={btnStyle('#4fc3f7', '#fff', loading)}>
            {loading ? '导入中...' : '导入'}
          </button>
        </div>
      </div>
    </div>
  );
}

function btnStyle(bg: string, color: string, disabled = false): React.CSSProperties {
  return {
    padding: '8px 24px', borderRadius: 6, border: 'none',
    background: disabled ? '#e8e8e8' : bg, color: disabled ? '#bbb' : color,
    fontSize: 14, fontWeight: 600, cursor: disabled ? 'not-allowed' : 'pointer',
  };
}
