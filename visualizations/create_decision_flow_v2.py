"""
Decision Flow Diagram - GO/CANARY/HOLD Logic - Dark Theme with Japanese Font Support
Shows the automated decision-making process based on CAS, ROI, and Risk
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import matplotlib.lines as mlines
from diagram_config import setup_japanese_font, DARK_THEME, FONT_SIZES, setup_dark_theme, get_text_kwargs, has_japanese

# Setup Japanese font
japanese_font = setup_japanese_font()

# Increased figure size by 20%
fig, ax = plt.subplots(1, 1, figsize=(21.6, 15.6))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
ax.axis('off')

# Apply dark theme
setup_dark_theme(fig, ax)

# Title
ax.text(9, 12.5, 'CQOx Decision Flow: Automated GO/CANARY/HOLD Logic',
        **get_text_kwargs(japanese_font, 'title', weight='bold'), ha='center')
ax.text(9, 12, 'Evidence-based policy approval with multi-dimensional quality gates',
        **get_text_kwargs(japanese_font, 'subtitle', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# === Input: Policy Card ===
y_input = 10.5
input_box = FancyBboxPatch((3, y_input), 12, 1.2, boxstyle="round,pad=0.15",
                           edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                           alpha=0.7, linewidth=2.5)
ax.add_patch(input_box)
ax.text(9, y_input+0.9, 'INPUT: Policy Card from Causal Analysis',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')
ax.text(9, y_input+0.45, 'Metrics: CAS Score, Δ¥, ROI, CVaR (Risk), Sample Size, Balance, Overlap',
        **get_text_kwargs(japanese_font, 'label'), ha='center')

# Arrow down
arrow1 = FancyArrowPatch((9, y_input-0.05), (9, 9.8),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow1)

# === Decision Diamond 1: CAS Score Check ===
y_d1 = 8.5
diamond1 = Polygon([(9, y_d1+1.2), (11, y_d1+0.6), (9, y_d1), (7, y_d1+0.6)],
                   closed=True, edgecolor=DARK_THEME['accent_blue'],
                   facecolor=DARK_THEME['accent_yellow'], alpha=0.3, linewidth=2.5)
ax.add_patch(diamond1)
ax.text(9, y_d1+0.8, 'CAS Score?',
        **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(9, y_d1+0.4, '(Quality Gate)',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# CAS >= 0.8 (High Quality)
ax.text(11.5, y_d1+0.6, 'CAS ≥ 0.8',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_green'], 'bold'))
arrow_high = FancyArrowPatch((11.1, y_d1+0.6), (13, y_d1+0.6),
                            arrowstyle='->', mutation_scale=20, linewidth=2.5,
                            color=DARK_THEME['accent_green'])
ax.add_patch(arrow_high)

# CAS 0.6-0.8 (Medium Quality)
arrow_mid = FancyArrowPatch((9, y_d1-0.05), (9, 7.3),
                           arrowstyle='->', mutation_scale=20, linewidth=2.5,
                           color=DARK_THEME['accent_orange'])
ax.add_patch(arrow_mid)
ax.text(9.5, y_d1-0.3, '0.6 ≤ CAS < 0.8',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_orange'], 'bold'))

# CAS < 0.6 (Low Quality)
ax.text(6.5, y_d1+0.6, 'CAS < 0.6',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_red'], 'bold'))
arrow_low = FancyArrowPatch((6.9, y_d1+0.6), (5, y_d1+0.6),
                           arrowstyle='->', mutation_scale=20, linewidth=2.5,
                           color=DARK_THEME['accent_red'])
ax.add_patch(arrow_low)

# === High CAS Path: Diamond 2 (ROI Check) ===
y_d2 = 8.5
diamond2 = Polygon([(14.5, y_d2+1.2), (16.5, y_d2+0.6), (14.5, y_d2), (12.5, y_d2+0.6)],
                   closed=True, edgecolor=DARK_THEME['accent_green'],
                   facecolor=DARK_THEME['accent_green'], alpha=0.3, linewidth=2.5)
ax.add_patch(diamond2)
ax.text(14.5, y_d2+0.8, 'ROI > 1.5?',
        **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(14.5, y_d2+0.4, '(Profitability)',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# ROI > 1.5: Arrow down to GO
arrow_roi_yes = FancyArrowPatch((14.5, y_d2-0.05), (14.5, 6.8),
                               arrowstyle='->', mutation_scale=20, linewidth=2.5,
                               color=DARK_THEME['accent_green'])
ax.add_patch(arrow_roi_yes)
ax.text(14.9, y_d2-0.3, 'Yes',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_green'], 'bold'))

# ROI <= 1.5: Arrow to CANARY
arrow_roi_no = FancyArrowPatch((12.4, y_d2+0.6), (10.5, y_d2+0.6),
                              arrowstyle='->', mutation_scale=20, linewidth=2.5,
                              color=DARK_THEME['accent_orange'])
ax.add_patch(arrow_roi_no)
ax.text(11.5, y_d2+0.9, 'No (ROI ≤ 1.5)',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_orange'], 'bold'))

# Redirect to CANARY box
arrow_roi_no_down = FancyArrowPatch((10.5, y_d2+0.5), (10.5, 6.8),
                                   arrowstyle='->', mutation_scale=20, linewidth=2.5,
                                   color=DARK_THEME['accent_orange'])
ax.add_patch(arrow_roi_no_down)

# === Medium CAS Path: Diamond 3 (Risk Check) ===
y_d3 = 6.5
diamond3 = Polygon([(9, y_d3+0.7), (10.2, y_d3+0.15), (9, y_d3-0.4), (7.8, y_d3+0.15)],
                   closed=True, edgecolor=DARK_THEME['accent_orange'],
                   facecolor=DARK_THEME['accent_yellow'], alpha=0.3, linewidth=2.5)
ax.add_patch(diamond3)
ax.text(9, y_d3+0.35, 'Risk?',
        **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(9, y_d3-0.05, '(CVaR)',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# Low Risk: CANARY
arrow_risk_low = FancyArrowPatch((9, y_d3-0.45), (9, 5.8),
                                arrowstyle='->', mutation_scale=20, linewidth=2.5,
                                color=DARK_THEME['accent_orange'])
ax.add_patch(arrow_risk_low)
ax.text(9.5, y_d3-0.7, 'Low Risk',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_orange'], 'bold'))

# High Risk: HOLD
arrow_risk_high = FancyArrowPatch((7.7, y_d3+0.15), (5.5, y_d3+0.15),
                                 arrowstyle='->', mutation_scale=20, linewidth=2.5,
                                 color=DARK_THEME['accent_red'])
ax.add_patch(arrow_risk_high)
ax.text(6.5, y_d3+0.4, 'High Risk',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_red'], 'bold'))

# Redirect to HOLD
arrow_risk_hold_down = FancyArrowPatch((5.5, y_d3+0.05), (5.5, 5.8),
                                      arrowstyle='->', mutation_scale=20, linewidth=2.5,
                                      color=DARK_THEME['accent_red'])
ax.add_patch(arrow_risk_hold_down)

# === Low CAS Path: Direct to HOLD ===
arrow_low_cas = FancyArrowPatch((5, y_d1+0.5), (5, 5.8),
                               arrowstyle='->', mutation_scale=20, linewidth=2.5,
                               color=DARK_THEME['accent_red'])
ax.add_patch(arrow_low_cas)

# === FINAL OUTPUTS ===
y_out = 4
# GO Box
go_box = FancyBboxPatch((12.5, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                        edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['accent_green'],
                        alpha=0.5, linewidth=3)
ax.add_patch(go_box)
ax.text(14.5, y_out+1.25, '✓ GO',
        **get_text_kwargs(japanese_font, 'heading', DARK_THEME['background'], 'bold'),
        ha='center')
ax.text(14.5, y_out+0.85, 'Deploy to 100%',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['background']), ha='center')
ax.text(14.5, y_out+0.5, 'High Quality + High ROI',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(14.5, y_out+0.15, 'Full Production',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# CANARY Box
canary_box = FancyBboxPatch((7, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                            edgecolor=DARK_THEME['accent_orange'], facecolor=DARK_THEME['accent_orange'],
                            alpha=0.5, linewidth=3)
ax.add_patch(canary_box)
ax.text(9, y_out+1.25, '⚠ CANARY',
        **get_text_kwargs(japanese_font, 'heading', DARK_THEME['background'], 'bold'),
        ha='center')
ax.text(9, y_out+0.85, 'Test on 10-20%',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['background']), ha='center')
ax.text(9, y_out+0.5, 'Medium Quality / ROI',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(9, y_out+0.15, 'Gradual Rollout',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# HOLD Box
hold_box = FancyBboxPatch((1.5, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                          edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['accent_red'],
                          alpha=0.5, linewidth=3)
ax.add_patch(hold_box)
ax.text(3.5, y_out+1.25, '✗ HOLD',
        **get_text_kwargs(japanese_font, 'heading', DARK_THEME['background'], 'bold'),
        ha='center')
ax.text(3.5, y_out+0.85, 'Do NOT Deploy',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['background']), ha='center')
ax.text(3.5, y_out+0.5, 'Low Quality / High Risk',
        **get_text_kwargs(japanese_font, 'body'), ha='center')
ax.text(3.5, y_out+0.15, 'Re-design needed',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# === Detailed Criteria Box ===
criteria_box = FancyBboxPatch((0.5, 0.3), 17, 2.8, boxstyle="round,pad=0.15",
                              edgecolor=DARK_THEME['text_secondary'], facecolor=DARK_THEME['box_data'],
                              alpha=0.7, linewidth=2)
ax.add_patch(criteria_box)
ax.text(9, 2.9, 'Detailed Decision Criteria',
        **get_text_kwargs(japanese_font, 'heading', weight='bold'), ha='center')

# GO Criteria
ax.text(1, 2.5, 'GO Criteria:',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_green'], 'bold'))
go_criteria = [
    '• CAS ≥ 0.8 (High causal confidence)',
    '• ROI > 1.5 (Strong profitability)',
    '• CVaR within acceptable range',
    '• Balance SMD < 0.1',
    '• Overlap check passed',
    '• Sample size > min threshold'
]
for i, crit in enumerate(go_criteria):
    ax.text(1.2, 2.2 - i*0.25, crit, **get_text_kwargs(japanese_font, 'body'))

# CANARY Criteria
ax.text(7, 2.5, 'CANARY Criteria:',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_orange'], 'bold'))
canary_criteria = [
    '• 0.6 ≤ CAS < 0.8 (Medium confidence)',
    '• ROI > 1.0 but ≤ 1.5',
    '• Moderate risk (CVaR acceptable)',
    '• Some diagnostic warnings',
    '• Requires monitoring',
    '• Test on small segment first'
]
for i, crit in enumerate(canary_criteria):
    ax.text(7.2, 2.2 - i*0.25, crit, **get_text_kwargs(japanese_font, 'body'))

# HOLD Criteria
ax.text(13, 2.5, 'HOLD Criteria:',
        **get_text_kwargs(japanese_font, 'label', DARK_THEME['accent_red'], 'bold'))
hold_criteria = [
    '• CAS < 0.6 (Low confidence)',
    '• ROI ≤ 1.0 or negative Δ¥',
    '• High CVaR (unacceptable risk)',
    '• Failed balance/overlap checks',
    '• Sensitivity tests failed',
    '• Governance violations'
]
for i, crit in enumerate(hold_criteria):
    ax.text(13.2, 2.2 - i*0.25, crit, **get_text_kwargs(japanese_font, 'body'))

# Footer note
ax.text(9, 0.1, 'Note: All decisions are logged with full audit trail for compliance and reproducibility',
        **get_text_kwargs(japanese_font, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=DARK_THEME['accent_yellow'], alpha=0.3))

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/decision_flow_logic.png',
            dpi=300, bbox_inches='tight', facecolor=DARK_THEME['background'])
print("✓ Decision Flow Logic diagram created: Picture/decision_flow_logic.png")
