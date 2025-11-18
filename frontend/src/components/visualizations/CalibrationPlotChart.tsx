/**
 * Calibration Plot Chart
 * CATE予測値と実測値の較正プロット
 */

import { useEffect, useRef } from 'react';

interface CalibrationPlotChartProps {
  predictedCate: number[];
  observedCate: number[];
}

export default function CalibrationPlotChart({
  predictedCate,
  observedCate,
}: CalibrationPlotChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (
      !canvasRef.current ||
      predictedCate.length === 0 ||
      observedCate.length === 0
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
    const allValues = [...predictedCate, ...observedCate];
    const minVal = Math.min(...allValues);
    const maxVal = Math.max(...allValues);
    const range = maxVal - minVal;
    const plotMin = minVal - range * 0.1;
    const plotMax = maxVal + range * 0.1;

    const xScale = (x: number) =>
      padding + ((x - plotMin) / (plotMax - plotMin)) * (width - 2 * padding);
    const yScale = (y: number) =>
      height -
      padding -
      ((y - plotMin) / (plotMax - plotMin)) * (height - 2 * padding);

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

    // Draw perfect calibration line (diagonal)
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(xScale(plotMin), yScale(plotMin));
    ctx.lineTo(xScale(plotMax), yScale(plotMax));
    ctx.stroke();
    ctx.setLineDash([]);

    // Calculate calibration curve (binned)
    const nBins = 10;
    const binEdges = Array.from({ length: nBins + 1 }, (_, i) =>
      plotMin + (i * (plotMax - plotMin)) / nBins
    );
    const binMeans: Array<{ predicted: number; observed: number; count: number }> = [];

    for (let i = 0; i < nBins; i++) {
      const binPredicted: number[] = [];
      const binObserved: number[] = [];

      predictedCate.forEach((pred, idx) => {
        if (pred >= binEdges[i] && pred < binEdges[i + 1]) {
          binPredicted.push(pred);
          binObserved.push(observedCate[idx]);
        }
      });

      if (binPredicted.length > 0) {
        binMeans.push({
          predicted:
            binPredicted.reduce((a, b) => a + b, 0) / binPredicted.length,
          observed:
            binObserved.reduce((a, b) => a + b, 0) / binObserved.length,
          count: binPredicted.length,
        });
      }
    }

    // Draw calibration curve
    if (binMeans.length > 0) {
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 3;
      ctx.beginPath();
      binMeans.forEach((bin, index) => {
        const x = xScale(bin.predicted);
        const y = yScale(bin.observed);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw points
      binMeans.forEach((bin) => {
        const x = xScale(bin.predicted);
        const y = yScale(bin.observed);
        const radius = 3 + Math.sqrt(bin.count) / 2;

        ctx.fillStyle = '#22d3ee';
        ctx.strokeStyle = '#0e7490';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      });
    }

    // Draw scatter plot (semi-transparent)
    ctx.fillStyle = 'rgba(96, 165, 250, 0.3)';
    predictedCate.forEach((pred, idx) => {
      const obs = observedCate[idx];
      const x = xScale(pred);
      const y = yScale(obs);
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Predicted CATE', width / 2, height - 10);

    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Observed CATE', 0, 0);
    ctx.restore();

    // Draw axis markers
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const val = plotMin + (i * (plotMax - plotMin)) / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(val.toFixed(2), x, height - padding + 20);

      const y = height - padding - (i * (height - 2 * padding)) / 5;
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(2), padding - 10, y + 4);
    }

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
    ctx.fillText('Calibration', legendX + 25, legendY + 11);

    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 27);
    ctx.lineTo(legendX + 20, legendY + 27);
    ctx.stroke();
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Perfect', legendX + 25, legendY + 31);
    ctx.setLineDash([]);
  }, [predictedCate, observedCate]);

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
