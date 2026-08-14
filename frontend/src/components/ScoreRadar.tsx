import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { DIMENSIONS } from '../types';

interface Props {
  scores: Record<string, number>;
  height?: number;
}

export default function ScoreRadar({ scores, height = 300 }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);

    const indicators = DIMENSIONS.map(d => ({
      name: d.label, max: 10,
    }));

    const values = DIMENSIONS.map(d => scores[d.key] || 0);

    chart.setOption({
      radar: {
        indicator: indicators,
        center: ['50%', '52%'],
        radius: '65%',
        axisName: { fontSize: 11, color: '#555' },
      },
      series: [{
        type: 'radar',
        data: [{ value: values, name: '得分', areaStyle: { color: 'rgba(79, 195, 247, 0.25)' } }],
        lineStyle: { color: '#4fc3f7', width: 2 },
        itemStyle: { color: '#4fc3f7' },
        symbol: 'circle',
        symbolSize: 4,
      }],
    });

    return () => chart.dispose();
  }, [scores]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
}
