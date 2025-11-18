/**
 * Enhanced Pareto Frontier Chart with CAS Quality Overlay
 * PDFの指摘に対応: CAS/Quality指標をプロットに重ねて表示
 */

import { useEffect, useRef, useState } from 'react';

interface PolicyData {
  name: string;
  profit: number;
  risk: number;
  cas?: number; // Causal Assurance Score
  deltaProfit?: number;
  deltaRisk?: number;
  isParetoEfficient?: boolean;
}

interface EnhancedParetoChartProps {
  policies: PolicyData[];
  onSelectPolicy?: (policy: PolicyData) => void;
  selectedPolicy?: string | null;
}

export default function EnhancedParetoChart({
  policies,
  onSelectPolicy,
  selectedPolicy,
}: EnhancedParetoChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredPolicy, setHoveredPolicy] = useState<PolicyData | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

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
    const padding = 80;

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

    // Draw Pareto frontier line
    const efficientPolicies = policies.filter(p => p.isParetoEfficient);
    if (efficientPolicies.length > 0) {
      const sorted = [...efficientPolicies].sort((a, b) => a.risk - b.risk);
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 3;
      ctx.setLineDash([5, 5]);
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
      ctx.setLineDash([]);
    }

    // Draw policy points with CAS-based coloring
    policies.forEach((policy) => {
      const x = xScale(policy.risk);
      const y = yScale(policy.profit);
      const cas = policy.cas || 0;

      // Color based on CAS score
      let color;
      if (cas >= 0.8) {
        color = '#10b981'; // Green - High quality
      } else if (cas >= 0.6) {
        color = '#f59e0b'; // Yellow - Medium quality
      } else {
        color = '#ef4444'; // Red - Low quality
      }

      // Size based on profit magnitude
      const baseSize = 8;
      const sizeMultiplier = 1 + (policy.profit / maxProfit) * 0.5;
      const size = baseSize * sizeMultiplier;

      // Highlight selected or efficient
      const isSelected = policy.name === selectedPolicy;
      const isEfficient = policy.isParetoEfficient;

      if (isSelected) {
        // Selected policy - large with white border
        ctx.fillStyle = color;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, size + 4, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      } else if (isEfficient) {
        // Efficient policy - ring style
        ctx.fillStyle = color;
        ctx.strokeStyle = '#22d3ee';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      } else {
        // Dominated policy - semi-transparent
        ctx.fillStyle = color + '99';
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.fill();
      }

      // Draw policy label for efficient policies
      if (isEfficient || isSelected) {
        ctx.fillStyle = '#f1f5f9';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(policy.name, x, y - size - 8);
      }
    });

    // Draw labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Risk →', width / 2, height - 20);

    ctx.save();
    ctx.translate(25, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('← Profit (¥)', 0, 0);
    ctx.restore();

    // Draw axis values
    ctx.font = '11px monospace';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 5; i++) {
      const profit = minProfit + (i * (maxProfit - minProfit)) / 5;
      const y = height - padding - (i * (height - 2 * padding)) / 5;
      ctx.textAlign = 'right';
      ctx.fillText(`¥${(profit / 1000000).toFixed(1)}M`, padding - 10, y + 4);

      const risk = minRisk + (i * (maxRisk - minRisk)) / 5;
      const x = padding + (i * (width - 2 * padding)) / 5;
      ctx.textAlign = 'center';
      ctx.fillText(risk.toFixed(2), x, height - padding + 25);
    }

    // Draw legend
    const legendX = width - 180;
    const legendY = padding + 20;

    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('CAS Quality:', legendX, legendY);

    // CAS color scale
    const casColors = [
      { color: '#10b981', label: '≥0.8 High' },
      { color: '#f59e0b', label: '0.6-0.8 Med' },
      { color: '#ef4444', label: '<0.6 Low' },
    ];

    casColors.forEach((item, i) => {
      const y = legendY + 25 + i * 20;
      ctx.fillStyle = item.color;
      ctx.beginPath();
      ctx.arc(legendX + 5, y, 6, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText(item.label, legendX + 18, y + 4);
    });

    // Frontier legend
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 95);
    ctx.lineTo(legendX + 20, legendY + 95);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Pareto Frontier', legendX + 25, legendY + 99);

  }, [policies, selectedPolicy]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setMousePos({ x: e.clientX, y: e.clientY });

    // Check if hovering over a policy
    const padding = 80;
    const width = rect.width;
    const height = rect.height;

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

    let found: PolicyData | null = null;
    for (const policy of policies) {
      const px = xScale(policy.risk);
      const py = yScale(policy.profit);
      const dist = Math.sqrt((x - px) ** 2 + (y - py) ** 2);
      if (dist < 15) {
        found = policy;
        break;
      }
    }

    setHoveredPolicy(found);
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (hoveredPolicy && onSelectPolicy) {
      onSelectPolicy(hoveredPolicy);
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '500px' }}>
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        style={{
          width: '100%',
          height: '100%',
          cursor: hoveredPolicy ? 'pointer' : 'default',
        }}
      />

      {/* Tooltip */}
      {hoveredPolicy && (
        <div
          style={{
            position: 'fixed',
            left: mousePos.x + 15,
            top: mousePos.y + 15,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '12px',
            color: '#f1f5f9',
            fontSize: '13px',
            pointerEvents: 'none',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          }}
        >
          <div style={{ fontWeight: '700', marginBottom: '8px', fontSize: '14px' }}>
            {hoveredPolicy.name}
          </div>
          <div style={{ display: 'grid', gap: '4px' }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Profit: </span>
              <span style={{ fontWeight: '600' }}>¥{(hoveredPolicy.profit / 1000000).toFixed(2)}M</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Risk: </span>
              <span style={{ fontWeight: '600' }}>{hoveredPolicy.risk.toFixed(3)}</span>
            </div>
            {hoveredPolicy.cas !== undefined && (
              <div>
                <span style={{ color: '#94a3b8' }}>CAS: </span>
                <span
                  style={{
                    fontWeight: '600',
                    color:
                      hoveredPolicy.cas >= 0.8
                        ? '#10b981'
                        : hoveredPolicy.cas >= 0.6
                        ? '#f59e0b'
                        : '#ef4444',
                  }}
                >
                  {hoveredPolicy.cas.toFixed(2)}
                </span>
              </div>
            )}
            {hoveredPolicy.deltaProfit !== undefined && (
              <div>
                <span style={{ color: '#94a3b8' }}>Δ¥ vs Baseline: </span>
                <span style={{ fontWeight: '600', color: '#10b981' }}>
                  +¥{(hoveredPolicy.deltaProfit / 1000000).toFixed(2)}M
                </span>
              </div>
            )}
            {hoveredPolicy.isParetoEfficient && (
              <div
                style={{
                  marginTop: '4px',
                  padding: '4px 8px',
                  background: 'rgba(34, 211, 238, 0.2)',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: '#22d3ee',
                  textAlign: 'center',
                }}
              >
                ✓ Pareto Efficient
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
