import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchJob, updateJob, updateJobStatus } from '../api';
import type { Application } from '../types';
import { DIMENSIONS, VERDICT_COLORS } from '../types';
import ScoreRadar from '../components/ScoreRadar';
import ScoreBar from '../components/ScoreBar';
import StatusBadge from '../components/StatusBadge';
import StatusTimeline from '../components/StatusTimeline';

const VALID_STATUSES = ['已投递', '已读', '筛过', '笔试', '一面', '二面', '三面', 'HR面', 'Offer', '入职', '已拒', '挂掉'];

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!id) return;
    fetchJob(id).then(data => {
      setJob(data);
      setNotes(data.notes || '');
      setLoading(false);
    });
  }, [id]);

  if (loading) return <p style={{ textAlign: 'center', padding: 60, color: '#999' }}>加载中...</p>;
  if (!job) return <p style={{ textAlign: 'center', padding: 60, color: '#f5222d' }}>未找到岗位</p>;

  async function handleStatusChange(newStatus: string) {
    if (!id) return;
    const updated = await updateJobStatus(id, newStatus);
    setJob(updated);
  }

  async function handleSaveNotes() {
    if (!id) return;
    const updated = await updateJob(id, { notes });
    setJob(updated);
    setEditingNotes(false);
  }

  const scoresMap: Record<string, number> = {
    score_hard: job.scores.score_hard,
    score_project: job.scores.score_project,
    score_level: job.scores.score_level,
    score_salary: job.scores.score_salary,
    score_scale: job.scores.score_scale,
    score_growth: job.scores.score_growth,
    score_jd_match: job.scores.score_jd_match,
  };

  const verdictColor = VERDICT_COLORS[job.verdict] || '#8c8c8c';

  return (
    <div>
      {/* 返回按钮 */}
      <button onClick={() => navigate('/jobs')} style={{
        padding: '6px 16px', borderRadius: 6, border: 'none', background: '#e8e8e8',
        color: '#333', fontSize: 13, cursor: 'pointer', marginBottom: 16,
      }}>
        ← 返回列表
      </button>

      {/* 头部信息 */}
      <div style={{
        background: '#fff', borderRadius: 10, padding: 24, marginBottom: 20,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h2 style={{ fontSize: 22, marginBottom: 4 }}>{job.position}</h2>
            <p style={{ fontSize: 16, color: '#555' }}>{job.company}</p>
            <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 13, color: '#888', flexWrap: 'wrap' }}>
              <span>📍 {job.location || '-'}{job.location_bonus > 0 ? ` (+${job.location_bonus} 广深加分)` : ''}</span>
              <span>💰 {job.salary_range || '-'}</span>
              <span>📅 {job.date || '-'}</span>
              <span>📡 {job.channel || '-'}</span>
              <span>📄 简历: {job.resume_version || 'v1'}</span>
              {job.url && (
                <a href={job.url} target="_blank" rel="noopener noreferrer"
                  style={{ color: '#4fc3f7' }}>🔗 职位链接</a>
              )}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <StatusBadge status={job.status} />
            <div style={{ marginTop: 12 }}>
              <select
                value=""
                onChange={e => { if (e.target.value) handleStatusChange(e.target.value); }}
                style={{
                  padding: '6px 12px', borderRadius: 6, border: '1px solid #d9d9d9',
                  fontSize: 13, background: '#fff', cursor: 'pointer',
                }}
              >
                <option value="">更新状态...</option>
                {VALID_STATUSES.filter(s => s !== job.status).map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* 七维打分 */}
        <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: 16, marginBottom: 16 }}>🎯 七维打分</h3>

          {/* 雷达图 */}
          <ScoreRadar scores={scoresMap} height={260} />

          {/* 总分 */}
          <div style={{ textAlign: 'center', margin: '12px 0' }}>
            <span style={{ fontSize: 13, color: '#888' }}>
              七维小计：{job.scores.total_score - job.scores.location_bonus}/70
              {job.scores.location_bonus > 0 && ` + 地点加分：${job.scores.location_bonus}`}
            </span>
            <div style={{ fontSize: 32, fontWeight: 700, color: verdictColor }}>
              {job.scores.total_score}
              <span style={{ fontSize: 14, fontWeight: 500 }}>
                /71 {job.verdict}
              </span>
            </div>
          </div>

          {/* 逐维度得分条 */}
          <div style={{ marginTop: 4 }}>
            {DIMENSIONS.map(d => (
              <ScoreBar key={d.key} label={d.label} score={scoresMap[d.key] || 0} />
            ))}
          </div>
        </div>

        {/* 状态时间线 + 备注 */}
        <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: 16, marginBottom: 16 }}>📜 状态变更记录</h3>
          <StatusTimeline history={job.status_history} />

          <div style={{ marginTop: 20, borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ fontSize: 16 }}>📝 备注</h3>
              {!editingNotes && (
                <button onClick={() => setEditingNotes(true)} style={{
                  padding: '4px 12px', borderRadius: 4, border: '1px solid #d9d9d9',
                  background: '#fff', fontSize: 12, cursor: 'pointer',
                }}>
                  编辑
                </button>
              )}
            </div>
            {editingNotes ? (
              <div>
                <textarea
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  rows={4}
                  style={{
                    width: '100%', padding: 10, borderRadius: 6, border: '1px solid #d9d9d9',
                    fontSize: 13, resize: 'vertical',
                  }}
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 8, justifyContent: 'flex-end' }}>
                  <button onClick={() => { setNotes(job.notes || ''); setEditingNotes(false); }} style={{
                    padding: '6px 16px', borderRadius: 4, border: '1px solid #d9d9d9',
                    background: '#fff', fontSize: 12, cursor: 'pointer',
                  }}>
                    取消
                  </button>
                  <button onClick={handleSaveNotes} style={{
                    padding: '6px 16px', borderRadius: 4, border: 'none', background: '#4fc3f7',
                    color: '#fff', fontSize: 12, cursor: 'pointer',
                  }}>
                    保存
                  </button>
                </div>
              </div>
            ) : (
              <p style={{ fontSize: 13, color: '#666', whiteSpace: 'pre-wrap', minHeight: 40 }}>
                {job.notes || '暂无备注'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* 公司调研卡片 */}
      {(job.research_core_business || job.research_tech_stack || job.research_team_features ||
        job.research_match_advantages || job.research_weakness_strategy) && (
        <div style={{
          background: '#fff', borderRadius: 10, padding: 20, marginTop: 20,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>
          <h3 style={{ fontSize: 16, marginBottom: 16 }}>🔍 公司调研</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
            {[
              ['🏢 核心业务', job.research_core_business],
              ['🛠 技术栈', job.research_tech_stack],
              ['👥 团队特点', job.research_team_features],
              ['✅ 匹配优势', job.research_match_advantages],
              ['⚠️ 短板应对', job.research_weakness_strategy],
            ].map(([label, value]) => value && (
              <div key={label} style={{
                padding: 14, background: '#fafafa', borderRadius: 8,
                border: '1px solid #f0f0f0',
              }}>
                <div style={{ fontSize: 12, color: '#888', marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 13, color: '#333', lineHeight: 1.6 }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
