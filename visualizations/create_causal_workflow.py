"""
Causal Inference Workflow Diagram
Shows the detailed flow from data to causal estimates with all estimators
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.lines as mlines

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')

# Colors
c_input = '#4CAF50'
c_process = '#2196F3'
c_estimator = '#FF9800'
c_diagnostic = '#9C27B0'
c_output = '#F44336'

# Title
ax.text(10, 13.5, 'CQOx Causal Inference Workflow', fontsize=26, fontweight='bold', ha='center')
ax.text(10, 13, 'From Raw Data to Actionable Causal Estimates', fontsize=13, ha='center', style='italic', color='gray')

# === Step 1: Data Input ===
y1 = 11.5
input_box = FancyBboxPatch((0.5, y1), 3, 1.2, boxstyle="round,pad=0.1",
                           edgecolor=c_input, facecolor=c_input, alpha=0.3, linewidth=2.5)
ax.add_patch(input_box)
ax.text(2, y1+0.95, 'Step 1: Data Input', fontsize=12, fontweight='bold', ha='center')
ax.text(2, y1+0.6, 'CSV Upload / DWH', fontsize=9, ha='center')
ax.text(2, y1+0.25, 'Raw Marketing Data', fontsize=8, ha='center', style='italic')
ax.text(2, y1+0.05, '(user_id, treatment, outcome,', fontsize=7, ha='center', family='monospace')
ax.text(2, y1-0.1, 'covariates, timestamp)', fontsize=7, ha='center', family='monospace')

# Arrow 1->2
arrow1 = FancyArrowPatch((3.6, y1+0.6), (4.9, y1+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow1)

# === Step 2: Schema Detection & Validation ===
y2 = 11.5
schema_box = FancyBboxPatch((5, y2), 3.5, 1.2, boxstyle="round,pad=0.1",
                            edgecolor=c_process, facecolor=c_process, alpha=0.3, linewidth=2.5)
ax.add_patch(schema_box)
ax.text(6.75, y2+0.95, 'Step 2: Schema Detection', fontsize=12, fontweight='bold', ha='center')
ax.text(6.75, y2+0.6, 'Auto-detect columns:', fontsize=9, ha='center')
ax.text(6.75, y2+0.25, '✓ Treatment (T)', fontsize=8, ha='center')
ax.text(6.75, y2+0.05, '✓ Outcome (Y)', fontsize=8, ha='center')
ax.text(6.75, y2-0.15, '✓ Covariates (X)', fontsize=8, ha='center')

# Arrow 2->3
arrow2 = FancyArrowPatch((8.6, y2+0.6), (9.9, y2+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow2)

# === Step 3: Causal Design ===
y3 = 11.5
design_box = FancyBboxPatch((10, y3), 3.5, 1.2, boxstyle="round,pad=0.1",
                            edgecolor=c_process, facecolor=c_process, alpha=0.3, linewidth=2.5)
ax.add_patch(design_box)
ax.text(11.75, y3+0.95, 'Step 3: Causal Design', fontsize=12, fontweight='bold', ha='center')
ax.text(11.75, y3+0.6, 'User confirms/adjusts:', fontsize=9, ha='center')
ax.text(11.75, y3+0.3, '• Column mapping', fontsize=8, ha='center')
ax.text(11.75, y3+0.05, '• Estimator selection', fontsize=8, ha='center')
ax.text(11.75, y3-0.15, '• Analysis unit', fontsize=8, ha='center')

# Arrow 3->4
arrow3 = FancyArrowPatch((13.6, y3+0.6), (14.9, y3+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow3)

# === Step 4: Train Models Button ===
y4 = 11.5
train_box = FancyBboxPatch((15, y4), 2.5, 1.2, boxstyle="round,pad=0.1",
                           edgecolor='#4CAF50', facecolor='#4CAF50', alpha=0.5, linewidth=3)
ax.add_patch(train_box)
ax.text(16.25, y4+0.7, '🚀 Train Models', fontsize=13, fontweight='bold', ha='center', color='white')
ax.text(16.25, y4+0.3, 'Triggers async', fontsize=9, ha='center', color='white')
ax.text(16.25, y4+0.05, 'Celery task', fontsize=9, ha='center', color='white')

# Downward arrow to estimators
arrow4_down = FancyArrowPatch((16.25, y4-0.15), (10, 9.8),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow4_down)

# === Step 5: Parallel Estimator Execution ===
y5 = 7.5
ax.text(10, 9.5, 'Step 4: Parallel Causal Estimation (7 Estimators)',
        fontsize=13, fontweight='bold', ha='center')
ax.text(10, 9.15, 'Each estimator runs independently and produces CATE + confidence intervals',
        fontsize=10, ha='center', style='italic', color='gray')

# 7 Estimators
estimators = [
    ('Doubly Robust (DR)', 1.5, y5+1, 'Combines PS + OR\nRobust to model\nmisspecification'),
    ('IPW', 4.5, y5+1, 'Inverse Propensity\nWeighting\nReweights samples'),
    ('DiD', 7.5, y5+1, 'Difference-in-\nDifferences\nPre/post comparison'),
    ('IV', 10.5, y5+1, 'Instrumental\nVariable\nHandles unmeasured\nconfounding'),
    ('Causal Forest', 13.5, y5+1, 'ML-based CATE\nHeterogeneous\neffects'),
    ('SCM', 16.5, y5+1, 'Synthetic Control\nConstructs\ncounterfactual'),
    ('RD', 19, y5+1, 'Regression\nDiscontinuity\nCutoff-based')
]

for i, (name, x, y, desc) in enumerate(estimators):
    # Estimator box
    est_box = FancyBboxPatch((x-0.95, y-0.3), 1.9, 1.4, boxstyle="round,pad=0.08",
                             edgecolor=c_estimator, facecolor=c_estimator, alpha=0.3, linewidth=2)
    ax.add_patch(est_box)
    ax.text(x, y+0.9, name, fontsize=9, fontweight='bold', ha='center')
    ax.text(x, y+0.3, desc, fontsize=7, ha='center', va='center', style='italic')

    # Output arrow
    arrow_est = FancyArrowPatch((x, y-0.35), (x, y5-0.2),
                               arrowstyle='->', mutation_scale=15, linewidth=1.5,
                               color=c_estimator, alpha=0.7)
    ax.add_patch(arrow_est)

# === Step 6: Aggregation ===
y6 = 6.5
agg_box = FancyBboxPatch((3, y6), 14, 0.8, boxstyle="round,pad=0.1",
                         edgecolor=c_process, facecolor=c_process, alpha=0.3, linewidth=2.5)
ax.add_patch(agg_box)
ax.text(10, y6+0.55, 'Step 5: Result Aggregation & Ensemble', fontsize=12, fontweight='bold', ha='center')
ax.text(10, y6+0.15, 'Combine estimates | Compute meta-learner consensus | Calculate uncertainty bounds',
        fontsize=9, ha='center')

# Arrow to diagnostics
arrow5_down = FancyArrowPatch((10, y6-0.05), (10, 5.55),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow5_down)

# === Step 7: Diagnostic Checks ===
y7 = 3.5
ax.text(10, 5.3, 'Step 6: Diagnostic Validation', fontsize=13, fontweight='bold', ha='center')
ax.text(10, 5, 'Comprehensive quality checks before presenting results',
        fontsize=10, ha='center', style='italic', color='gray')

diagnostics = [
    ('Overlap\nCheck', 2, y7, 'Positivity\nPropensity\nDistribution'),
    ('Balance\nCheck', 4.5, y7, 'SMD < 0.1\nLove Plot\nCovariate\nBalance'),
    ('Sensitivity\nAnalysis', 7, y7, 'Rosenbaum Γ\nE-value\nHidden Bias'),
    ('Refutation\nTests', 9.5, y7, 'Placebo Test\nRandom\nConfounder'),
    ('CATE\nValidation', 12, y7, 'Qini Curve\nUplift Model\nPerformance'),
    ('Consistency\nCheck', 14.5, y7, 'Cross-\nEstimator\nAgreement'),
    ('Sample\nSize', 17, y7, 'Power\nAnalysis\nMin N')
]

for name, x, y, detail in diagnostics:
    diag_box = FancyBboxPatch((x-0.9, y-0.2), 1.8, 1.2, boxstyle="round,pad=0.08",
                              edgecolor=c_diagnostic, facecolor=c_diagnostic, alpha=0.3, linewidth=2)
    ax.add_patch(diag_box)
    ax.text(x, y+0.75, name, fontsize=9, fontweight='bold', ha='center')
    ax.text(x, y+0.15, detail, fontsize=7, ha='center', va='center')

    # Arrow down
    arrow_diag = FancyArrowPatch((x, y-0.25), (x, 2.45),
                                arrowstyle='->', mutation_scale=12, linewidth=1.2,
                                color=c_diagnostic, alpha=0.6)
    ax.add_patch(arrow_diag)

# === Step 8: CAS Score Calculation ===
y8 = 1.5
cas_box = FancyBboxPatch((3, y8), 14, 0.8, boxstyle="round,pad=0.1",
                         edgecolor=c_output, facecolor=c_output, alpha=0.3, linewidth=2.5)
ax.add_patch(cas_box)
ax.text(10, y8+0.55, 'Step 7: CAS Score Calculation (Causal Assurance Score)',
        fontsize=12, fontweight='bold', ha='center')
ax.text(10, y8+0.15, 'Aggregate diagnostics → CAS ∈ [0,1] | CAS ≥ 0.8 → GO | 0.6-0.8 → CANARY | < 0.6 → HOLD',
        fontsize=8.5, ha='center')

# === Step 9: Final Output ===
y9 = 0.3
output_box = FancyBboxPatch((1, y9), 18, 0.8, boxstyle="round,pad=0.1",
                            edgecolor=c_output, facecolor=c_output, alpha=0.4, linewidth=3)
ax.add_patch(output_box)
ax.text(10, y9+0.5, 'Step 8: Output → Policy Cards (Δ¥, ROI, Risk, CAS, GO/CANARY/HOLD)',
        fontsize=12, fontweight='bold', ha='center', color='white')

# Arrow CAS -> Output
arrow_final = FancyArrowPatch((10, y8-0.05), (10, y9+0.85),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow_final)

# Add legend explaining key metrics
legend_box = FancyBboxPatch((0.3, 10), 4, 1.3, boxstyle="round,pad=0.1",
                            edgecolor='gray', facecolor='lightyellow', alpha=0.7, linewidth=1.5)
ax.add_patch(legend_box)
ax.text(2.3, 11.15, 'Key Metrics Explained', fontsize=10, fontweight='bold', ha='center')
ax.text(0.5, 10.75, '• Δ¥: Incremental profit (treatment effect)', fontsize=7.5, ha='left')
ax.text(0.5, 10.5, '• CATE: Conditional Average Treatment Effect', fontsize=7.5, ha='left')
ax.text(0.5, 10.25, '• CAS: Causal Assurance Score (quality)', fontsize=7.5, ha='left')
ax.text(0.5, 10.0, '• SMD: Standardized Mean Difference', fontsize=7.5, ha='left')

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/causal_inference_workflow.png', dpi=300, bbox_inches='tight')
print("✓ Causal Inference Workflow diagram created: Picture/causal_inference_workflow.png")
