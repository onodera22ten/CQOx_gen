/**
 * Overlap Density Chart
 * 傾向スコアの重なりを表示
 */

import { useEffect, useRef } from 'react';

interface OverlapDensityChartProps {
  propensityScoresTreatment: number[];
  propensityScoresControl: number[];
}

export default function OverlapDensityChart({
  propensityScoresTreatment,
  propensityScoresControl,
}: OverlapDensityChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (
      !canvasRef.current ||
      propensityScoresTreatment.length === 0 ||
      propensityScoresControl.length === 0
    )
      return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;
    const padding = 60;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Calculate histogram bins
    const bins = 40;
    const histTreatment = new Array(bins).fill(0);
    const histControl = new Array(bins).fill(0);

    propensityScoresTreatment.forEach((score) => {
      const bin = Math.min(Math.floor(score * bins), bins - 1);
      histTreatment[bin]++;
    });

    propensityScoresControl.forEach((score) => {
      const bin = Math.min(Math.floor(score * bins), bins - 1);
      histControl[bin]++;
    });

    // Normalize histograms
    const maxTreatment = Math.max(...histTreatment);
    const maxControl = Math.max(...histControl);
    const maxCount = Math.max(maxTreatment, maxControl);

    const normTreatment = histTreatment.map((v) => v / maxCount);
    const normControl = histControl.map((v) => v / maxCount);

    // Draw grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i * (height - 2 * padding)) / 5;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Draw histograms
    const barWidth = (width - 2 * padding) / bins;

    // Treatment histogram
    ctx.fillStyle = 'rgba(59, 130, 246, 0.5)';
    normTreatment.forEach((value, index) => {
      const x = padding + index * barWidth;
      const barHeight = value * (height - 2 * padding);
      const y = height - padding - barHeight;
      ctx.fillRect(x, y, barWidth - 1, barHeight);
    });

    // Control histogram
    ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
    normControl.forEach((value, index) => {
      const x = padding + index * barWidth;
      const barHeight = value * (height - 2 * padding);
      const y = height - padding - barHeight;
      ctx.fillRect(x, y, barWidth - 1, barHeight);
    });

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Propensity Score', width / 2, height - 10);

    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Density', 0, 0);
    ctx.restore();

    // Draw axis markers
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const score = i / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(score.toFixed(1), x, height - padding + 20);
    }

    // Draw legend
    const legendX = width - padding - 120;
    const legendY = padding + 10;

    ctx.fillStyle = 'rgba(59, 130, 246, 0.7)';
    ctx.fillRect(legendX, legendY, 20, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.textAlign = 'left';
    ctx.font = '12px sans-serif';
    ctx.fillText('Treatment', legendX + 25, legendY + 12);

    ctx.fillStyle = 'rgba(239, 68, 68, 0.7)';
    ctx.fillRect(legendX, legendY + 25, 20, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Control', legendX + 25, legendY + 37);
  }, [propensityScoresTreatment, propensityScoresControl]);

  return (
    <div
      style={{
        width: '100%',
        height: '500px',
        background: 'rgba(15, 23, 42, 0.6)',
        borderRadius: '8px',
        padding: '16px',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
}
