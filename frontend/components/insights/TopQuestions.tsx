'use client';

import { Chart as ChartJS, BarElement, CategoryScale, Legend, LinearScale, Tooltip, TooltipItem } from 'chart.js';
import { Bar } from 'react-chartjs-2';

import { LENA_ACCENT, LENA_GRID, LENA_TICKS } from '../../lib/theme';

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
        backgroundColor: LENA_ACCENT,
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
      tooltip: { callbacks: { label: (ctx: TooltipItem<'bar'>) => `${ctx.formattedValue} questions` } },
    },
  } as const;

  return (
    <div className="h-64">
      <Bar data={data} options={options} aria-label="Top questions asked this term" />
    </div>
  );
}
