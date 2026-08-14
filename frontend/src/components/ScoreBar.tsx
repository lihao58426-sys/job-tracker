interface Props {
  label: string;
  score: number;
  max?: number;
}

const barColors = ['#52c41a', '#73d13d', '#bae637', '#faad14', '#ff7a45', '#f5222d'];

export default function ScoreBar({ label, score, max = 10 }: Props) {
  const pct = Math.min(score / max, 1);
  const colorIdx = Math.min(Math.floor((1 - pct) * barColors.length), barColors.length - 1);
  const color = barColors[colorIdx];

  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2, fontSize: 12, color: '#555' }}>
        <span>{label}</span>
        <span style={{ fontWeight: 600 }}>{score}/{max}</span>
      </div>
      <div style={{ height: 8, background: '#e8e8e8', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct * 100}%`, background: color,
          borderRadius: 4, transition: 'width 0.3s',
        }} />
      </div>
    </div>
  );
}
