import { STATUS_COLORS } from '../types';

interface Props {
  status: string;
}

export default function StatusBadge({ status }: Props) {
  const color = STATUS_COLORS[status] || '#8c8c8c';
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 10,
      fontSize: 12, fontWeight: 600, color: '#fff', backgroundColor: color,
      whiteSpace: 'nowrap',
    }}>
      {status}
    </span>
  );
}
