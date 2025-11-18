/**
 * Sensitivity Gamma Chart
 * 未観測交絡に対する感度分析
 */

import { useEffect, useRef } from 'react';

interface SensitivityGammaChartProps {
  gammaValues: number[];
  pValues: number[];
}

export default function SensitivityGammaChart({
  gammaValues,
  pValues,
}: SensitivityGammaChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (
      !canvasRef.current ||
      gammaValues.length === 0 ||
      pValues.length === 0
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

    // Calculate ranges
    const minGamma = Math.min(...gammaValues);
    const maxGamma = Math.max(...gammaValues);
    // const minP = 0; // unused
    const maxP = 1;

    const xScale = (gamma: number) =>
      padding +
      ((gamma - minGamma) / (maxGamma - minGamma || 1)) *
        (width - 2 * padding);
    const yScale = (p: number) =>
      height - padding - (p / maxP) * (height - 2 * padding);

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

    // Draw significance threshold (p = 0.05)
    const threshold = 0.05;
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding, yScale(threshold));
    ctx.lineTo(width - padding, yScale(threshold));
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw sensitivity curve
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 3;
    ctx.beginPath();

    // Sort by gamma
    const sorted = gammaValues
      .map((gamma, i) => ({ gamma, p: pValues[i] }))
      .sort((a, b) => a.gamma - b.gamma);

    sorted.forEach((point, index) => {
      const x = xScale(point.gamma);
      const y = yScale(point.p);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw points
    sorted.forEach((point) => {
      const x = xScale(point.gamma);
      const y = yScale(point.p);

      const isSignificant = point.p < threshold;
      ctx.fillStyle = isSignificant ? '#22c55e' : '#ef4444';
      ctx.strokeStyle = isSignificant ? '#166534' : '#991b1b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // Find critical gamma (where p-value crosses threshold)
    let criticalGamma: number | null = null;
    for (let i = 0; i < sorted.length - 1; i++) {
      if (
        (sorted[i].p < threshold && sorted[i + 1].p >= threshold) ||
        (sorted[i].p >= threshold && sorted[i + 1].p < threshold)
      ) {
        // Linear interpolation
        const t =
          (threshold - sorted[i].p) / (sorted[i + 1].p - sorted[i].p);
        criticalGamma =
          sorted[i].gamma + t * (sorted[i + 1].gamma - sorted[i].gamma);
        break;
      }
    }

    // Draw critical gamma line
    if (criticalGamma !== null) {
      ctx.strokeStyle = '#eab308';
      ctx.lineWidth = 2;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xScale(criticalGamma), padding);
      ctx.lineTo(xScale(criticalGamma), height - padding);
      ctx.stroke();
      ctx.setLineDash([]);

      // Label critical gamma
      ctx.fillStyle = '#eab308';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(
        `Γ* = ${criticalGamma.toFixed(2)}`,
        xScale(criticalGamma),
        padding - 10
      );
    }

    // Shade robust region (p < 0.05)
    const robustPoints = sorted.filter((p) => p.p < threshold);
    if (robustPoints.length > 0) {
      ctx.fillStyle = 'rgba(34, 197, 94, 0.1)';
      ctx.beginPath();
      ctx.moveTo(xScale(robustPoints[0].gamma), yScale(threshold));

      robustPoints.forEach((point) => {
        ctx.lineTo(xScale(point.gamma), yScale(point.p));
      });

      ctx.lineTo(
        xScale(robustPoints[robustPoints.length - 1].gamma),
        yScale(threshold)
      );
      ctx.closePath();
      ctx.fill();
    }

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Sensitivity Parameter (Γ)', width / 2, height - 10);

    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('P-Value', 0, 0);
    ctx.restore();

    // Draw axis markers
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const gamma = minGamma + (i * (maxGamma - minGamma)) / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(gamma.toFixed(1), x, height - padding + 20);

      const p = (i * maxP) / 5;
      const y = height - padding - (i * (height - 2 * padding)) / 5;
      ctx.textAlign = 'right';
      ctx.fillText(p.toFixed(2), padding - 10, y + 4);
    }

    // Draw threshold label
    ctx.fillStyle = '#ef4444';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('α = 0.05', width - padding + 5, yScale(threshold) + 4);

    // Draw legend
    const legendX = width - padding - 160;
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
    ctx.fillText('Sensitivity', legendX + 25, legendY + 11);

    ctx.fillStyle = 'rgba(34, 197, 94, 0.3)';
    ctx.fillRect(legendX, legendY + 20, 20, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Robust Region', legendX + 25, legendY + 32);
  }, [gammaValues, pValues]);

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
