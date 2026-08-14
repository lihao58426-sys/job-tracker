import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchDashboard, fetchFunnel } from '../api';
import type { DashboardStats, FunnelItem } from '../types';
import FunnelChart from '../components/FunnelChart';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [funnel, setFunnel] = useState<FunnelItem[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard().then(setStats);
    fetchFunnel().then(setFunnel);
  }, []);

  if (!stats) return <p style={{ textAlign: 'center', padding: 60, color: '#999' }}>加载中...</p>;

  const cards = [
    { label: '累计投递', value: stats.total, color: '#4fc3f7' },
    { label: '进行中', value: stats.active, color: '#faad14' },
    { label: '面试中', value: stats.interviewing, color: '#eb2f96' },
    { label: 'Offer', value: stats.offered, color: '#52c41a' },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 20, fontSize: 22 }}>📊 求职仪表盘</h2>

      {/* 统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {cards.map(c => (
          <div key={c.label} style={{
            background: '#fff', borderRadius: 10, padding: '20px 24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderTop: `3px solid ${c.color}`,
          }}>
            <div style={{ fontSize: 13, color: '#888', marginBottom: 8 }}>{c.label}</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* 投递漏斗 */}
        <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>📈 投递漏斗</h3>
          {funnel.length > 0 ? (
            <FunnelChart data={funnel} />
          ) : (
            <p style={{ color: '#999', fontSize: 13, textAlign: 'center', padding: 40 }}>暂无数据</p>
          )}
        </div>

        {/* 优先级 Top 5 */}
        <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>⭐ 优先级 Top 5</h3>
          {stats.top5.length === 0 ? (
            <p style={{ color: '#999', fontSize: 13, textAlign: 'center', padding: 40 }}>暂无投递</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {stats.top5.map((job, i) => (
                <div
                  key={job.id}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                    borderRadius: 8, cursor: 'pointer', background: '#fafafa',
                    border: '1px solid #f0f0f0', transition: 'background 0.2s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#f0f9ff')}
                  onMouseLeave={e => (e.currentTarget.style.background = '#fafafa')}
                >
                  <span style={{
                    width: 24, height: 24, borderRadius: '50%', background: '#4fc3f7',
                    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontWeight: 700,
                  }}>
                    {i + 1}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {job.company}
                    </div>
                    <div style={{ fontSize: 12, color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {job.position}
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: '#888' }}>{job.location}</span>
                  <span style={{
                    fontSize: 18, fontWeight: 700,
                    color: job.total_score >= 50 ? '#52c41a' : job.total_score >= 40 ? '#faad14' : '#f5222d',
                  }}>
                    {job.total_score}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 地点分布 */}
      {Object.keys(stats.by_location).length > 0 && (
        <div style={{ background: '#fff', borderRadius: 10, padding: 20, marginTop: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>📍 地点分布</h3>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {Object.entries(stats.by_location).map(([city, count]) => (
              <div key={city} style={{
                padding: '8px 18px', borderRadius: 20, background: city.includes('上海') || city.includes('杭州') ? '#e6f7ff' : '#f5f5f5',
                fontSize: 13, fontWeight: 500,
                border: city.includes('上海') || city.includes('杭州') ? '1px solid #91d5ff' : '1px solid #e8e8e8',
              }}>
                {city} × {count}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
