// ConfidenceChart.tsx – plots confidence scores over time for qualitative tracking.
'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

interface ConfidenceChartProps {
  labels: string[];
  values: number[];
}

export default function ConfidenceChart({ labels, values }: ConfidenceChartProps) {
  const data = {
    labels,
    datasets: [
      {
        label: 'Average confidence',
        data: values,
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.15)',
        fill: true,
        tension: 0.3,
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
        suggestedMax: 1,
        ticks: {
          callback: (value: any) => `${Math.round(Number(value) * 100)}%`,
          color: '#475569',
        },
        grid: { color: '#e2e8f0' },
      },
      x: {
        ticks: { color: '#475569' },
        grid: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${Math.round(Number(ctx.parsed.y) * 100)}% confidence`,
        },
      },
    },
  } as const;

  return (
    <div className="h-64">
      <Line data={data} options={options} aria-label="Confidence trend over time" />
    </div>
  );
}
