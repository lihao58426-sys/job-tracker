import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchJobs, updateJobStatus, deleteJob, batchDeleteJobs } from '../api';
import type { ApplicationListItem } from '../types';
import { VERDICT_COLORS } from '../types';
import StatusBadge from '../components/StatusBadge';
import ImportDialog from '../components/ImportDialog';

const VALID_STATUSES = ['未投递', '已投递', '已读', '筛过', '笔试', '一面', '二面', '三面', 'HR面', 'Offer', '入职', '已拒', '挂掉'];

export default function JobList() {
  const [jobs, setJobs] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // 多选
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 筛选
  const [filterStatus, setFilterStatus] = useState('');
  const [filterVerdict, setFilterVerdict] = useState('');
  const [filterLocation, setFilterLocation] = useState('');
  const [searchText, setSearchText] = useState('');

  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (filterStatus) params.status = filterStatus;
    if (filterVerdict) params.verdict = filterVerdict;
    if (filterLocation) params.location = filterLocation;
    if (searchText) params.search = searchText;
    const data = await fetchJobs(params);
    setJobs(data);
    setSelectedIds(new Set());
    setLoading(false);
  }, [filterStatus, filterVerdict, filterLocation, searchText]);

  useEffect(() => { load(); }, [load]);

  // 单选
  function toggleSelect(id: string) {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // 全选/取消全选
  function toggleSelectAll() {
    if (selectedIds.size === jobs.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(jobs.map(j => j.id)));
    }
  }

  // 批量更新状态
  async function handleBatchStatus(newStatus: string) {
    if (selectedIds.size === 0) return;
    if (!confirm(`将 ${selectedIds.size} 条记录的状态改为"${newStatus}"？`)) return;
    for (const id of selectedIds) {
      await updateJobStatus(id, newStatus);
    }
    setSelectedIds(new Set());
    load();
  }

  // 批量删除
  async function handleBatchDelete() {
    if (selectedIds.size === 0) return;
    if (!confirm(`确定删除选中的 ${selectedIds.size} 条记录？此操作不可恢复！`)) return;
    try {
      const res = await batchDeleteJobs(Array.from(selectedIds));
      if (res.errors?.length) {
        alert(`部分删除失败:\n${res.errors.join('\n')}`);
      }
      setSelectedIds(new Set());
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        || (err instanceof Error ? err.message : String(err));
      alert(`批量删除失败：${detail}`);
    }
  }

  // 单条操作
  async function handleStatusChange(id: string, newStatus: string) {
    await updateJobStatus(id, newStatus);
    load();
  }

  async function handleDelete(id: string) {
    if (!confirm(`确定删除 ${id}？`)) return;
    await deleteJob(id);
    load();
  }

  const verdictColor = (v: string) => VERDICT_COLORS[v] || '#8c8c8c';
  const allSelected = jobs.length > 0 && selectedIds.size === jobs.length;
  const someSelected = selectedIds.size > 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 22 }}>
          📋 岗位列表
          <span style={{ fontSize: 14, color: '#888', fontWeight: 400, marginLeft: 8 }}>
            共 {jobs.length} 条{someSelected && ` | 已选 ${selectedIds.size} 条`}
          </span>
        </h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setShowImport(true)} style={btnPrimary}>
            📥 导入 JSON
          </button>
        </div>
      </div>

      {/* 批量操作栏 */}
      {someSelected && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12,
          padding: '10px 16px', background: '#e6f7ff', borderRadius: 8,
          border: '1px solid #91d5ff',
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#0050b3' }}>
            已选 {selectedIds.size} 条
          </span>
          <select
            value=""
            onChange={e => { if (e.target.value) handleBatchStatus(e.target.value); }}
            style={{ padding: '4px 10px', borderRadius: 4, border: '1px solid #91d5ff', fontSize: 12, background: '#fff' }}
          >
            <option value="">批量改状态...</option>
            {VALID_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={handleBatchDelete} style={{
            padding: '4px 14px', borderRadius: 4, border: 'none', background: '#f5222d',
            color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}>
            🗑 批量删除
          </button>
          <button onClick={() => setSelectedIds(new Set())} style={{
            padding: '4px 14px', borderRadius: 4, border: '1px solid #d9d9d9',
            background: '#fff', fontSize: 12, cursor: 'pointer', marginLeft: 'auto',
          }}>
            取消选择
          </button>
        </div>
      )}

      {/* 筛选栏 */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          placeholder="🔍 搜索公司/岗位..."
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          style={inputStyle}
        />
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
          <option value="">全部状态</option>
          {VALID_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={filterVerdict} onChange={e => setFilterVerdict(e.target.value)} style={selectStyle}>
          <option value="">全部评级</option>
          <option value="高度适配">🟢 高度适配</option>
          <option value="中度适配">🟡 中度适配</option>
          <option value="不推荐投递">🔴 不推荐</option>
        </select>
        <select value={filterLocation} onChange={e => setFilterLocation(e.target.value)} style={selectStyle}>
          <option value="">全部地点</option>
          <option value="上海">📍 上海</option>
          <option value="杭州">📍 杭州</option>
          <option value="北京">北京</option>
          <option value="广州">广州</option>
          <option value="深圳">深圳</option>
        </select>
      </div>

      {/* 表格 */}
      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', overflow: 'auto' }}>
        {loading ? (
          <p style={{ textAlign: 'center', padding: 40, color: '#999' }}>加载中...</p>
        ) : jobs.length === 0 ? (
          <p style={{ textAlign: 'center', padding: 40, color: '#999' }}>暂无匹配的岗位记录</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#fafafa', borderBottom: '2px solid #f0f0f0' }}>
                <th style={{ ...thStyle, width: 40 }}>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    style={{ cursor: 'pointer', width: 15, height: 15 }}
                  />
                </th>
                <th style={thStyle}>#</th>
                <th style={{ ...thStyle, textAlign: 'left', minWidth: 120 }}>公司</th>
                <th style={{ ...thStyle, textAlign: 'left', minWidth: 160 }}>岗位</th>
                <th style={thStyle}>地点</th>
                <th style={thStyle}>薪资</th>
                <th style={thStyle}>总分</th>
                <th style={thStyle}>评级</th>
                <th style={thStyle}>进度</th>
                <th style={thStyle}>操作</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job, idx) => (
                <JobRow
                  key={job.id}
                  job={job}
                  rank={idx + 1}
                  isExpanded={expandedId === job.id}
                  isSelected={selectedIds.has(job.id)}
                  onToggle={() => setExpandedId(expandedId === job.id ? null : job.id)}
                  onSelect={() => toggleSelect(job.id)}
                  onStatusChange={s => handleStatusChange(job.id, s)}
                  onDelete={() => handleDelete(job.id)}
                  onDetail={() => navigate(`/jobs/${job.id}`)}
                  verdictColor={verdictColor(job.verdict)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ImportDialog open={showImport} onClose={() => setShowImport(false)} onSuccess={load} />
    </div>
  );
}

// ---- JobRow ----

function JobRow({ job, rank, isExpanded, isSelected, onToggle, onSelect, onStatusChange, onDelete, onDetail, verdictColor }: {
  job: ApplicationListItem;
  rank: number;
  isExpanded: boolean;
  isSelected: boolean;
  onToggle: () => void;
  onSelect: () => void;
  onStatusChange: (s: string) => void;
  onDelete: () => void;
  onDetail: () => void;
  verdictColor: string;
}) {
  const hasLocationBonus = job.location_bonus > 0;

  return (
    <>
      <tr
        onClick={onToggle}
        style={{
          borderBottom: '1px solid #f5f5f5', cursor: 'pointer',
          background: isExpanded ? '#f0f9ff' : isSelected ? '#fff7e6' : rank % 2 === 0 ? '#fafafa' : '#fff',
          transition: 'background 0.15s',
        }}
      >
        <td style={tdStyle} onClick={e => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            style={{ cursor: 'pointer', width: 15, height: 15 }}
          />
        </td>
        <td style={tdStyle}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 22, height: 22, borderRadius: '50%',
            background: rank <= 3 ? '#4fc3f7' : '#e8e8e8',
            color: rank <= 3 ? '#fff' : '#999', fontSize: 11, fontWeight: 700,
          }}>
            {rank}
          </span>
        </td>
        <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {job.company}
        </td>
        <td style={{ ...tdStyle, textAlign: 'left', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {job.position}
        </td>
        <td style={tdStyle}>
          {hasLocationBonus ? '📍 ' : ''}{job.location || '-'}
        </td>
        <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: 12 }}>{job.salary_range || '-'}</td>
        <td style={{ ...tdStyle, fontWeight: 700, fontSize: 15 }}>
          <span style={{ color: job.total_score >= 50 ? '#52c41a' : job.total_score >= 40 ? '#faad14' : '#f5222d' }}>
            {job.total_score}
          </span>
          {hasLocationBonus && <span style={{ fontSize: 10, color: '#4fc3f7', marginLeft: 2 }}>+{job.location_bonus}</span>}
        </td>
        <td style={tdStyle}>
          <span style={{
            display: 'inline-block', padding: '2px 8px', borderRadius: 4,
            fontSize: 11, fontWeight: 600, color: '#fff', background: verdictColor,
          }}>
            {job.verdict ? job.verdict.replace('投递', '') : '-'}
          </span>
        </td>
        <td style={tdStyle}><StatusBadge status={job.status} /></td>
        <td style={tdStyle} onClick={e => e.stopPropagation()}>
          <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
            <select
              value=""
              onChange={e => { if (e.target.value) onStatusChange(e.target.value); }}
              style={{ fontSize: 11, padding: '2px 4px', borderRadius: 4, border: '1px solid #d9d9d9', maxWidth: 56 }}
            >
              <option value="">改</option>
              {VALID_STATUSES.filter(s => s !== job.status).slice(0, 8).map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button onClick={onDetail} style={smallBtn('#4fc3f7')} title="详情">📋</button>
            {job.url && (
              <a href={job.url} target="_blank" rel="noopener noreferrer"
                style={{ ...smallBtn('#52c41a'), textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
                title="打开职位链接"
              >🔗</a>
            )}
            <button onClick={onDelete} style={smallBtn('#f5222d')} title="删除">🗑</button>
          </div>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={11} style={{ background: '#f0f9ff', padding: '16px 24px', borderBottom: '2px solid #bae7ff' }}>
            <ExpandedDetail job={job} />
          </td>
        </tr>
      )}
    </>
  );
}

// ---- Expanded Detail ----

function ExpandedDetail({ job }: { job: ApplicationListItem }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, fontSize: 13 }}>
      <div><strong>投递日期：</strong>{job.date || '-'}</div>
      <div><strong>渠道：</strong>{job.channel || '猎聘'}</div>
      <div><strong>薪资：</strong>{job.salary_range || '-'}</div>
      <div>
        <strong>地点：</strong>
        {job.location_bonus > 0 ? '📍 ' : ''}{job.location || '-'}
        {job.location_bonus > 0 && <span style={{ color: '#4fc3f7', marginLeft: 4 }}>(目标城市 +{job.location_bonus})</span>}
      </div>
      <div><strong>类型：</strong>{job.job_type || '-'}</div>
      <div>
        <strong>总分：</strong>
        <span style={{
          fontWeight: 700, fontSize: 16, marginLeft: 4,
          color: job.total_score >= 50 ? '#52c41a' : job.total_score >= 40 ? '#faad14' : '#f5222d',
        }}>
          {job.total_score}
        </span>
      </div>
      {job.url && (
        <div style={{ gridColumn: '1 / -1' }}>
          <strong>🔗 职位链接：</strong>
          <a href={job.url} target="_blank" rel="noopener noreferrer"
            style={{ color: '#1677ff', textDecoration: 'underline', wordBreak: 'break-all' }}>
            {job.url}
          </a>
        </div>
      )}
    </div>
  );
}

// ---- Styles ----

const thStyle: React.CSSProperties = {
  padding: '12px 10px', textAlign: 'center', fontSize: 12, fontWeight: 600, color: '#888',
  whiteSpace: 'nowrap',
};

const tdStyle: React.CSSProperties = {
  padding: '10px', textAlign: 'center', fontSize: 13,
};

const inputStyle: React.CSSProperties = {
  padding: '6px 12px', borderRadius: 6, border: '1px solid #d9d9d9',
  fontSize: 13, width: 200, outline: 'none',
};

const selectStyle: React.CSSProperties = {
  padding: '6px 12px', borderRadius: 6, border: '1px solid #d9d9d9',
  fontSize: 13, background: '#fff', cursor: 'pointer',
};

const btnPrimary: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none', background: '#4fc3f7',
  color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
};

function smallBtn(color: string): React.CSSProperties {
  return {
    padding: '2px 6px', borderRadius: 4, border: 'none', background: color,
    color: '#fff', fontSize: 12, cursor: 'pointer',
  };
}
