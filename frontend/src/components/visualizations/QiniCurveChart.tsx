/**
 * Qini Curve Chart
 * アップリフトモデル性能評価曲線
 */

import { useEffect, useRef } from 'react';

interface QiniCurveChartProps {
  upliftScores: number[];
  treatment: number[];
  outcomes: number[];
}

export default function QiniCurveChart({
  upliftScores,
  treatment,
  outcomes,
}: QiniCurveChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (
      !canvasRef.current ||
      upliftScores.length === 0 ||
      treatment.length === 0 ||
      outcomes.length === 0
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

    // Sort by uplift scores (descending)
    const indices = Array.from({ length: upliftScores.length }, (_, i) => i);
    indices.sort((a, b) => upliftScores[b] - upliftScores[a]);

    // Calculate Qini curve
    const n = indices.length;
    const qiniPoints: Array<{ x: number; y: number }> = [{ x: 0, y: 0 }];
    let cumTreatedPositive = 0;
    let cumTreated = 0;
    let cumControlPositive = 0;
    let cumControl = 0;

    indices.forEach((idx, i) => {
      const t = treatment[idx];
      const y = outcomes[idx];

      if (t === 1) {
        cumTreated++;
        if (y === 1) cumTreatedPositive++;
      } else {
        cumControl++;
        if (y === 1) cumControlPositive++;
      }

      const treatedRate = cumTreated > 0 ? cumTreatedPositive / cumTreated : 0;
      const controlRate = cumControl > 0 ? cumControlPositive / cumControl : 0;
      const qiniValue = cumTreated * treatedRate - cumControl * controlRate;

      qiniPoints.push({
        x: (i + 1) / n,
        y: qiniValue,
      });
    });

    // Calculate random baseline
    const totalTreated = treatment.reduce((a, b) => a + b, 0);
    const totalControl = n - totalTreated;
    const treatmentRate =
      treatment.reduce((a, b, i) => a + b * outcomes[i], 0) / totalTreated;
    const controlRate =
      treatment.reduce((a, b, i) => a + (1 - b) * outcomes[i], 0) / totalControl;

    const randomPoints: Array<{ x: number; y: number }> = [
      { x: 0, y: 0 },
      { x: 1, y: n * (treatmentRate - controlRate) },
    ];

    // Find max Y for scaling
    const maxY = Math.max(...qiniPoints.map((p) => p.y), ...randomPoints.map((p) => p.y));
    const minY = Math.min(...qiniPoints.map((p) => p.y), 0);

    const xScale = (x: number) => padding + x * (width - 2 * padding);
    const yScale = (y: number) =>
      height -
      padding -
      ((y - minY) / (maxY - minY || 1)) * (height - 2 * padding);

    // Draw grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i * (height - 2 * padding)) / 5;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();

      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
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

    // Draw random baseline
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    randomPoints.forEach((point, index) => {
      const x = xScale(point.x);
      const y = yScale(point.y);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Qini curve
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 3;
    ctx.beginPath();
    qiniPoints.forEach((point, index) => {
      const x = xScale(point.x);
      const y = yScale(point.y);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Find and mark optimal point
    const maxQini = Math.max(...qiniPoints.map((p) => p.y));
    const optimalPoint = qiniPoints.find((p) => p.y === maxQini);
    if (optimalPoint) {
      ctx.fillStyle = '#22c55e';
      ctx.beginPath();
      ctx.arc(xScale(optimalPoint.x), yScale(optimalPoint.y), 6, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Fraction of Population Targeted', width / 2, height - 10);

    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Qini Value', 0, 0);
    ctx.restore();

    // Draw axis markers
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const frac = i / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(frac.toFixed(1), x, height - padding + 20);

      const yVal = minY + (i * (maxY - minY)) / 5;
      const y = height - padding - (i * (height - 2 * padding)) / 5;
      ctx.textAlign = 'right';
      ctx.fillText(yVal.toFixed(0), padding - 10, y + 4);
    }

    // Draw legend
    const legendX = width - padding - 150;
    const legendY = padding + 10;

    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 7);
    ctx.lineTo(legendX + 20, legendY + 7);
    ctx.stroke();
    ctx.fillStyle = '#cbd5e1';
    ctx.textAlign = 'left';
    ctx.font = '12px sans-serif';
    ctx.fillText('Qini Curve', legendX + 25, legendY + 11);

    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 27);
    ctx.lineTo(legendX + 20, legendY + 27);
    ctx.stroke();
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Random', legendX + 25, legendY + 31);
    ctx.setLineDash([]);
  }, [upliftScores, treatment, outcomes]);

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
