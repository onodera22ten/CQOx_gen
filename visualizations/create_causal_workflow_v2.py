"""
Causal Inference Workflow Diagram - Dark Theme with Japanese Font Support
Shows the detailed flow from data to causal estimates with all estimators
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.lines as mlines
from diagram_config import setup_japanese_font, DARK_THEME, FONT_SIZES, setup_dark_theme, get_text_kwargs, has_japanese

# Setup Japanese font
japanese_font = setup_japanese_font()

# Increased figure size by 20%
fig, ax = plt.subplots(1, 1, figsize=(24, 16.8))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')

# Apply dark theme
setup_dark_theme(fig, ax)

# Title
ax.text(10, 13.5, 'CQOx Causal Inference Workflow',
        **get_text_kwargs(japanese_font, 'title', weight='bold'), ha='center')
ax.text(10, 13, 'From Raw Data to Actionable Causal Estimates',
        **get_text_kwargs(japanese_font, 'subtitle', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# === Step 1: Data Input ===
y1 = 11.5
input_box = FancyBboxPatch((0.5, y1), 3, 1.2, boxstyle="round,pad=0.1",
                           edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_data'],
                           alpha=0.7, linewidth=2.5)
ax.add_patch(input_box)
ax.text(2, y1+0.95, 'Step 1: Data Input',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(2, y1+0.6, 'CSV Upload / DWH',
        **get_text_kwargs(japanese_font, 'label'), ha='center')
ax.text(2, y1+0.25, 'Raw Marketing Data',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']), ha='center', style='italic')
ax.text(2, y1+0.05, '(user_id, treatment, outcome,',
        **get_text_kwargs(japanese_font, 'detail'), ha='center', family='monospace')
ax.text(2, y1-0.1, 'covariates, timestamp)',
        **get_text_kwargs(japanese_font, 'detail'), ha='center', family='monospace')

# Arrow 1->2
arrow1 = FancyArrowPatch((3.6, y1+0.6), (4.9, y1+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow1)

# === Step 2: Schema Detection & Validation ===
y2 = 11.5
schema_box = FancyBboxPatch((5, y2), 3.5, 1.2, boxstyle="round,pad=0.1",
                            edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                            alpha=0.7, linewidth=2.5)
ax.add_patch(schema_box)
ax.text(6.75, y2+0.95, 'Step 2: Schema Detection',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(6.75, y2+0.6, 'Auto-detect columns:',
        **get_text_kwargs(japanese_font, 'label'), ha='center')
ax.text(6.75, y2+0.25, '✓ Treatment (T)',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(6.75, y2+0.05, '✓ Outcome (Y)',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(6.75, y2-0.15, '✓ Covariates (X)',
        **get_text_kwargs(japanese_font, 'body'), ha='center')

# Arrow 2->3
arrow2 = FancyArrowPatch((8.6, y2+0.6), (9.9, y2+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow2)

# === Step 3: Causal Design ===
y3 = 11.5
design_box = FancyBboxPatch((10, y3), 3.5, 1.2, boxstyle="round,pad=0.1",
                            edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                            alpha=0.7, linewidth=2.5)
ax.add_patch(design_box)
ax.text(11.75, y3+0.95, 'Step 3: Causal Design',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(11.75, y3+0.6, 'User confirms/adjusts:',
        **get_text_kwargs(japanese_font, 'label'), ha='center')
ax.text(11.75, y3+0.3, '• Column mapping',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(11.75, y3+0.05, '• Estimator selection',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(11.75, y3-0.15, '• Analysis unit',
        **get_text_kwargs(japanese_font, 'body'), ha='center')

# Arrow 3->4
arrow3 = FancyArrowPatch((13.6, y3+0.6), (14.9, y3+0.6),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow3)

# === Step 4: Train Models Button ===
y4 = 11.5
train_box = FancyBboxPatch((15, y4), 2.5, 1.2, boxstyle="round,pad=0.1",
                           edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['accent_green'],
                           alpha=0.5, linewidth=3)
ax.add_patch(train_box)
ax.text(16.25, y4+0.7, '🚀 Train Models',
        **get_text_kwargs(japanese_font, 'heading', DARK_THEME['background'], 'bold'),
        ha='center')
ax.text(16.25, y4+0.3, 'Triggers async',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['background']), ha='center')
ax.text(16.25, y4+0.05, 'Celery task',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['background']), ha='center')

# Downward arrow to estimators
arrow4_down = FancyArrowPatch((16.25, y4-0.15), (10, 9.8),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow4_down)

# === Step 5: Parallel Estimator Execution ===
y5 = 7.5
ax.text(10, 9.5, 'Step 4: Parallel Causal Estimation (7 Estimators)',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(10, 9.15, 'Each estimator runs independently and produces CATE + confidence intervals',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')

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
                             edgecolor=DARK_THEME['accent_orange'], facecolor=DARK_THEME['box_causal'],
                             alpha=0.7, linewidth=2)
    ax.add_patch(est_box)
    ax.text(x, y+0.9, name,
            **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
    ax.text(x, y+0.3, desc,
            **get_text_kwargs(japanese_font, 'detail', DARK_THEME['text_secondary']),
            ha='center', va='center', style='italic')

    # Output arrow
    arrow_est = FancyArrowPatch((x, y-0.35), (x, y5-0.2),
                               arrowstyle='->', mutation_scale=15, linewidth=1.5,
                               color=DARK_THEME['accent_orange'], alpha=0.7)
    ax.add_patch(arrow_est)

# === Step 6: Aggregation ===
y6 = 6.5
agg_box = FancyBboxPatch((3, y6), 14, 0.8, boxstyle="round,pad=0.1",
                         edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                         alpha=0.7, linewidth=2.5)
ax.add_patch(agg_box)
ax.text(10, y6+0.55, 'Step 5: Result Aggregation & Ensemble',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(10, y6+0.15, 'Combine estimates | Compute meta-learner consensus | Calculate uncertainty bounds',
        **get_text_kwargs(japanese_font, 'label'), ha='center')

# Arrow to diagnostics
arrow5_down = FancyArrowPatch((10, y6-0.05), (10, 5.55),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow5_down)

# === Step 7: Diagnostic Checks ===
y7 = 3.5
ax.text(10, 5.3, 'Step 6: Diagnostic Validation',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(10, 5, 'Comprehensive quality checks before presenting results',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')

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
                              edgecolor=DARK_THEME['accent_purple'], facecolor=DARK_THEME['box_governance'],
                              alpha=0.7, linewidth=2)
    ax.add_patch(diag_box)
    ax.text(x, y+0.75, name,
            **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
    ax.text(x, y+0.15, detail,
            **get_text_kwargs(japanese_font, 'detail'), ha='center', va='center')

    # Arrow down
    arrow_diag = FancyArrowPatch((x, y-0.25), (x, 2.45),
                                arrowstyle='->', mutation_scale=12, linewidth=1.2,
                                color=DARK_THEME['accent_purple'], alpha=0.6)
    ax.add_patch(arrow_diag)

# === Step 8: CAS Score Calculation ===
y8 = 1.5
cas_box = FancyBboxPatch((3, y8), 14, 0.8, boxstyle="round,pad=0.1",
                         edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_decision'],
                         alpha=0.7, linewidth=2.5)
ax.add_patch(cas_box)
ax.text(10, y8+0.55, 'Step 7: CAS Score Calculation (Causal Assurance Score)',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(10, y8+0.15, 'Aggregate diagnostics → CAS ∈ [0,1] | CAS ≥ 0.8 → GO | 0.6-0.8 → CANARY | < 0.6 → HOLD',
        **get_text_kwargs(japanese_font, 'body'), ha='center')

# === Step 9: Final Output ===
y9 = 0.3
output_box = FancyBboxPatch((1, y9), 18, 0.8, boxstyle="round,pad=0.1",
                            edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['accent_red'],
                            alpha=0.6, linewidth=3)
ax.add_patch(output_box)
ax.text(10, y9+0.5, 'Step 8: Output → Policy Cards (Δ¥, ROI, Risk, CAS, GO/CANARY/HOLD)',
        **get_text_kwargs(japanese_font, 'heading', DARK_THEME['background'], 'bold'),
        ha='center')

# Arrow CAS -> Output
arrow_final = FancyArrowPatch((10, y8-0.05), (10, y9+0.85),
                             arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow_final)

# Add legend explaining key metrics
legend_box = FancyBboxPatch((0.3, 10), 4, 1.3, boxstyle="round,pad=0.1",
                            edgecolor=DARK_THEME['accent_yellow'], facecolor=DARK_THEME['box_export'],
                            alpha=0.7, linewidth=1.5)
ax.add_patch(legend_box)
ax.text(2.3, 11.15, 'Key Metrics Explained',
        **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(0.5, 10.75, '• Δ¥: Incremental profit (treatment effect)',
        **get_text_kwargs(japanese_font, 'body'), ha='left')
ax.text(0.5, 10.5, '• CATE: Conditional Average Treatment Effect',
        **get_text_kwargs(japanese_font, 'body'), ha='left')
ax.text(0.5, 10.25, '• CAS: Causal Assurance Score (quality)',
        **get_text_kwargs(japanese_font, 'body'), ha='left')
ax.text(0.5, 10.0, '• SMD: Standardized Mean Difference',
        **get_text_kwargs(japanese_font, 'body'), ha='left')

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/causal_inference_workflow.png',
            dpi=300, bbox_inches='tight', facecolor=DARK_THEME['background'])
print("✓ Causal Inference Workflow diagram created: Picture/causal_inference_workflow.png")
