'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TooltipItem,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

import { LENA_ACCENT, LENA_ACCENT_FILL, LENA_GRID, LENA_TICKS } from '../../lib/theme';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

interface DailyVolumeChartProps {
  labels: string[];
  values: number[];
}

export default function DailyVolumeChart({ labels, values }: DailyVolumeChartProps) {
  const data = {
    labels,
    datasets: [
      {
        label: 'Daily questions',
        data: values,
        borderColor: LENA_ACCENT,
        backgroundColor: LENA_ACCENT_FILL,
        fill: true,
        tension: 0.35,
        pointRadius: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: { precision: 0, color: LENA_TICKS },
        grid: { color: LENA_GRID },
      },
      x: {
        ticks: { color: LENA_TICKS },
        grid: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx: TooltipItem<'line'>) => `${ctx.formattedValue} questions` } },
    },
  } as const;

  return (
    <div className="h-64">
      <Line data={data} options={options} aria-label="Daily question volume" />
    </div>
  );
}
