import type { StatusHistory } from '../types';
import { STATUS_COLORS } from '../types';

interface Props {
  history: StatusHistory[];
}

export default function StatusTimeline({ history }: Props) {
  if (!history || history.length === 0) {
    return <p style={{ color: '#999', fontSize: 13 }}>暂无状态变更记录</p>;
  }

  return (
    <div style={{ position: 'relative', paddingLeft: 20 }}>
      {/* 竖线 */}
      <div style={{
        position: 'absolute', left: 5, top: 8, bottom: 8,
        width: 2, background: '#e8e8e8',
      }} />
      {history.map((h, i) => {
        const color = STATUS_COLORS[h.status] || '#8c8c8c';
        return (
          <div key={i} style={{ position: 'relative', marginBottom: 16, paddingLeft: 8 }}>
            {/* 圆点 */}
            <div style={{
              position: 'absolute', left: -19, top: 4,
              width: 10, height: 10, borderRadius: '50%',
              background: color,
            }} />
            <div style={{ fontSize: 13, fontWeight: 600, color: '#1a1a2e' }}>
              {h.status}
              <span style={{ fontWeight: 400, color: '#999', marginLeft: 8, fontSize: 12 }}>
                {h.date}
              </span>
            </div>
            {h.note && (
              <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                {h.note}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
