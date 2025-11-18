/**
 * Balance Plot (Love Plot)
 * 共変量バランスを表示
 */

import { useEffect, useRef } from 'react';

interface BalancePlotChartProps {
  variables: string[];
  smdValues: number[];
  threshold?: number;
}

export default function BalancePlotChart({
  variables,
  smdValues,
  threshold = 0.1,
}: BalancePlotChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || variables.length === 0) return;

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
    const padding = 80;
    const barHeight = Math.min(30, (height - 2 * padding) / variables.length);
    const maxSMD = Math.max(...smdValues.map(Math.abs), threshold * 2);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw threshold lines
    const xScale = (smd: number) =>
      padding + width / 2 - padding + (smd / maxSMD) * ((width - 2 * padding) / 2);

    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(xScale(threshold), padding);
    ctx.lineTo(xScale(threshold), height - padding);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(xScale(-threshold), padding);
    ctx.lineTo(xScale(-threshold), height - padding);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw center line
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(xScale(0), padding);
    ctx.lineTo(xScale(0), height - padding);
    ctx.stroke();

    // Draw bars
    variables.forEach((variable, index) => {
      const smd = smdValues[index];
      const y = padding + index * barHeight + barHeight / 2;
      const x0 = xScale(0);
      const x1 = xScale(smd);

      const isBalanced = Math.abs(smd) <= threshold;
      ctx.fillStyle = isBalanced ? '#22c55e' : '#ef4444';

      ctx.beginPath();
      ctx.rect(
        Math.min(x0, x1),
        y - barHeight / 4,
        Math.abs(x1 - x0),
        barHeight / 2
      );
      ctx.fill();

      // Draw point
      ctx.beginPath();
      ctx.arc(x1, y, 4, 0, 2 * Math.PI);
      ctx.fill();

      // Draw variable name
      ctx.fillStyle = '#cbd5e1';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(variable, padding - 10, y + 4);

      // Draw SMD value
      ctx.textAlign = 'left';
      ctx.fillText(smd.toFixed(3), x1 + 8, y + 4);
    });

    // Draw axis labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Standardized Mean Difference (SMD)', width / 2, height - 10);

    // Draw threshold labels
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#ef4444';
    ctx.fillText(`-${threshold}`, xScale(-threshold), padding - 10);
    ctx.fillText(`+${threshold}`, xScale(threshold), padding - 10);

    // Draw scale markers
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('0', xScale(0), padding - 10);

    // Draw legend
    const legendX = width - padding - 120;
    const legendY = padding;

    ctx.fillStyle = '#22c55e';
    ctx.fillRect(legendX, legendY, 15, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.textAlign = 'left';
    ctx.fillText('Balanced', legendX + 20, legendY + 12);

    ctx.fillStyle = '#ef4444';
    ctx.fillRect(legendX, legendY + 25, 15, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Imbalanced', legendX + 20, legendY + 37);
  }, [variables, smdValues, threshold]);

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
