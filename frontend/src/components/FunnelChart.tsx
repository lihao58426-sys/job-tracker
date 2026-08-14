import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { FunnelItem } from '../types';

interface Props {
  data: FunnelItem[];
  height?: number;
}

export default function FunnelChart({ data, height = 280 }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;
    const chart = echarts.init(chartRef.current);

    chart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'funnel',
        left: '15%',
        right: '15%',
        top: 20,
        bottom: 20,
        minSize: '20%',
        maxSize: '100%',
        gap: 4,
        label: { show: true, position: 'inside', fontSize: 13, fontWeight: 600 },
        labelLine: { show: false },
        data: data.map(d => ({ name: d.name, value: d.value })),
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
        },
        color: ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8'],
      }],
    });

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
}
