'use client';

import { Chart as ChartJS, BarElement, CategoryScale, Legend, LinearScale, Tooltip, TooltipItem } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface TopQuestionsProps {
  labels: string[];
  values: number[];
}

export default function TopQuestions({ labels, values }: TopQuestionsProps) {
  const data = {
    labels,
    datasets: [
      {
        label: 'Count',
        data: values,
        backgroundColor: '#1d4ed8',
        borderRadius: 12,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: { precision: 0, color: '#475569' },
        grid: { color: '#e2e8f0' },
      },
      x: {
        ticks: { color: '#475569' },
        grid: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx: TooltipItem<'bar'>) => `${ctx.formattedValue} questions` } },
    },
  } as const;

  return (
    <div className="h-64">
      <Bar data={data} options={options} aria-label="Top questions asked this term" />
    </div>
  );
}
