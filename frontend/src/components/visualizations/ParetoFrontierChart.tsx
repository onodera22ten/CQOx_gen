/**
 * Pareto Frontier Chart
 * ポリシーの利益-リスクトレードオフを表示
 */

import { useEffect, useRef } from 'react';
import { Policy } from '../../api/v1/visualizations';

interface ParetoFrontierChartProps {
  policies: Policy[];
  efficientFrontier?: Policy[];
  dominatedPolicies?: Policy[];
}

export default function ParetoFrontierChart({
  policies,
  efficientFrontier = [],
  dominatedPolicies = [],
}: ParetoFrontierChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || policies.length === 0) return;

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

    // Calculate scales
    const profits = policies.map((p) => p.profit);
    const risks = policies.map((p) => p.risk);
    const minProfit = Math.min(...profits, 0);
    const maxProfit = Math.max(...profits);
    const minRisk = Math.min(...risks, 0);
    const maxRisk = Math.max(...risks);

    const xScale = (risk: number) =>
      padding + ((risk - minRisk) / (maxRisk - minRisk || 1)) * (width - 2 * padding);
    const yScale = (profit: number) =>
      height - padding - ((profit - minProfit) / (maxProfit - minProfit || 1)) * (height - 2 * padding);

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

    // Draw efficient frontier line
    if (efficientFrontier.length > 0) {
      const sorted = [...efficientFrontier].sort((a, b) => a.risk - b.risk);
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 3;
      ctx.beginPath();
      sorted.forEach((policy, index) => {
        const x = xScale(policy.risk);
        const y = yScale(policy.profit);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
    }

    // Draw dominated policies
    dominatedPolicies.forEach((policy) => {
      const x = xScale(policy.risk);
      const y = yScale(policy.profit);

      ctx.fillStyle = 'rgba(239, 68, 68, 0.6)';
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw efficient policies
    efficientFrontier.forEach((policy) => {
      const x = xScale(policy.risk);
      const y = yScale(policy.profit);

      ctx.fillStyle = '#22d3ee';
      ctx.strokeStyle = '#0e7490';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // Draw all policies if no classification
    if (efficientFrontier.length === 0 && dominatedPolicies.length === 0) {
      policies.forEach((policy) => {
        const x = xScale(policy.risk);
        const y = yScale(policy.profit);

        ctx.fillStyle = '#60a5fa';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Risk', width / 2, height - 10);

    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Profit', 0, 0);
    ctx.restore();

    // Draw axis labels
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const profit = minProfit + (i * (maxProfit - minProfit)) / 5;
      const y = height - padding - (i * (height - 2 * padding)) / 5;
      ctx.textAlign = 'right';
      ctx.fillText(profit.toFixed(2), padding - 10, y + 4);

      const risk = minRisk + (i * (maxRisk - minRisk)) / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(risk.toFixed(2), x, height - padding + 20);
    }

    // Draw legend
    const legendX = width - padding - 150;
    const legendY = padding + 10;

    if (efficientFrontier.length > 0) {
      ctx.fillStyle = '#22d3ee';
      ctx.beginPath();
      ctx.arc(legendX, legendY, 6, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = '#cbd5e1';
      ctx.textAlign = 'left';
      ctx.font = '12px sans-serif';
      ctx.fillText('Efficient', legendX + 15, legendY + 4);
    }

    if (dominatedPolicies.length > 0) {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.6)';
      ctx.beginPath();
      ctx.arc(legendX, legendY + 25, 6, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText('Dominated', legendX + 15, legendY + 29);
    }
  }, [policies, efficientFrontier, dominatedPolicies]);

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
