"""
Decision Flow Diagram - GO/CANARY/HOLD Logic
Shows the automated decision-making process based on CAS, ROI, and Risk
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import matplotlib.lines as mlines

fig, ax = plt.subplots(1, 1, figsize=(18, 13))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
ax.axis('off')

# Colors
c_go = '#4CAF50'
c_canary = '#FFC107'
c_hold = '#F44336'
c_process = '#2196F3'

# Title
ax.text(9, 12.5, 'CQOx Decision Flow: Automated GO/CANARY/HOLD Logic',
        fontsize=24, fontweight='bold', ha='center')
ax.text(9, 12, 'Evidence-based policy approval with multi-dimensional quality gates',
        fontsize=12, ha='center', style='italic', color='gray')

# === Input: Policy Card ===
y_input = 10.5
input_box = FancyBboxPatch((3, y_input), 12, 1.2, boxstyle="round,pad=0.15",
                           edgecolor=c_process, facecolor=c_process, alpha=0.3, linewidth=2.5)
ax.add_patch(input_box)
ax.text(9, y_input+0.9, 'INPUT: Policy Card from Causal Analysis', fontsize=14, fontweight='bold', ha='center')
ax.text(9, y_input+0.45, 'Metrics: CAS Score, Δ¥, ROI, CVaR (Risk), Sample Size, Balance, Overlap',
        fontsize=10, ha='center')

# Arrow down
arrow1 = FancyArrowPatch((9, y_input-0.05), (9, 9.8),
                        arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
ax.add_patch(arrow1)

# === Decision Diamond 1: CAS Score Check ===
y_d1 = 8.5
diamond1 = Polygon([(9, y_d1+1.2), (11, y_d1+0.6), (9, y_d1), (7, y_d1+0.6)],
                   closed=True, edgecolor=c_process, facecolor='lightyellow', linewidth=2.5)
ax.add_patch(diamond1)
ax.text(9, y_d1+0.8, 'CAS Score?', fontsize=11, fontweight='bold', ha='center')
ax.text(9, y_d1+0.4, '(Quality Gate)', fontsize=9, ha='center', style='italic')

# CAS >= 0.8 (High Quality)
ax.text(11.5, y_d1+0.6, 'CAS ≥ 0.8', fontsize=10, fontweight='bold', color=c_go)
arrow_high = FancyArrowPatch((11.1, y_d1+0.6), (13, y_d1+0.6),
                            arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_go)
ax.add_patch(arrow_high)

# CAS 0.6-0.8 (Medium Quality)
arrow_mid = FancyArrowPatch((9, y_d1-0.05), (9, 7.3),
                           arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_canary)
ax.add_patch(arrow_mid)
ax.text(9.5, y_d1-0.3, '0.6 ≤ CAS < 0.8', fontsize=9, fontweight='bold', color=c_canary)

# CAS < 0.6 (Low Quality)
ax.text(6.5, y_d1+0.6, 'CAS < 0.6', fontsize=10, fontweight='bold', color=c_hold)
arrow_low = FancyArrowPatch((6.9, y_d1+0.6), (5, y_d1+0.6),
                           arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_hold)
ax.add_patch(arrow_low)

# === High CAS Path: Diamond 2 (ROI Check) ===
y_d2 = 8.5
diamond2 = Polygon([(14.5, y_d2+1.2), (16.5, y_d2+0.6), (14.5, y_d2), (12.5, y_d2+0.6)],
                   closed=True, edgecolor=c_go, facecolor='lightgreen', linewidth=2.5)
ax.add_patch(diamond2)
ax.text(14.5, y_d2+0.8, 'ROI > 1.5?', fontsize=11, fontweight='bold', ha='center')
ax.text(14.5, y_d2+0.4, '(Profitability)', fontsize=9, ha='center', style='italic')

# ROI > 1.5: Arrow down to GO
arrow_roi_yes = FancyArrowPatch((14.5, y_d2-0.05), (14.5, 6.8),
                               arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_go)
ax.add_patch(arrow_roi_yes)
ax.text(14.9, y_d2-0.3, 'Yes', fontsize=9, fontweight='bold', color=c_go)

# ROI <= 1.5: Arrow to CANARY
arrow_roi_no = FancyArrowPatch((12.4, y_d2+0.6), (10.5, y_d2+0.6),
                              arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_canary)
ax.add_patch(arrow_roi_no)
ax.text(11.5, y_d2+0.9, 'No (ROI ≤ 1.5)', fontsize=9, fontweight='bold', color=c_canary)

# Redirect to CANARY box
arrow_roi_no_down = FancyArrowPatch((10.5, y_d2+0.5), (10.5, 6.8),
                                   arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_canary)
ax.add_patch(arrow_roi_no_down)

# === Medium CAS Path: Diamond 3 (Risk Check) ===
y_d3 = 6.5
diamond3 = Polygon([(9, y_d3+0.7), (10.2, y_d3+0.15), (9, y_d3-0.4), (7.8, y_d3+0.15)],
                   closed=True, edgecolor=c_canary, facecolor='#FFF9C4', linewidth=2.5)
ax.add_patch(diamond3)
ax.text(9, y_d3+0.35, 'Risk?', fontsize=10, fontweight='bold', ha='center')
ax.text(9, y_d3-0.05, '(CVaR)', fontsize=8, ha='center', style='italic')

# Low Risk: CANARY
arrow_risk_low = FancyArrowPatch((9, y_d3-0.45), (9, 5.8),
                                arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_canary)
ax.add_patch(arrow_risk_low)
ax.text(9.5, y_d3-0.7, 'Low Risk', fontsize=9, fontweight='bold', color=c_canary)

# High Risk: HOLD
arrow_risk_high = FancyArrowPatch((7.7, y_d3+0.15), (5.5, y_d3+0.15),
                                 arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_hold)
ax.add_patch(arrow_risk_high)
ax.text(6.5, y_d3+0.4, 'High Risk', fontsize=9, fontweight='bold', color=c_hold)

# Redirect to HOLD
arrow_risk_hold_down = FancyArrowPatch((5.5, y_d3+0.05), (5.5, 5.8),
                                      arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_hold)
ax.add_patch(arrow_risk_hold_down)

# === Low CAS Path: Direct to HOLD ===
arrow_low_cas = FancyArrowPatch((5, y_d1+0.5), (5, 5.8),
                               arrowstyle='->', mutation_scale=20, linewidth=2.5, color=c_hold)
ax.add_patch(arrow_low_cas)

# === FINAL OUTPUTS ===
y_out = 4
# GO Box
go_box = FancyBboxPatch((12.5, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                        edgecolor=c_go, facecolor=c_go, alpha=0.4, linewidth=3)
ax.add_patch(go_box)
ax.text(14.5, y_out+1.25, '✓ GO', fontsize=16, fontweight='bold', ha='center', color='white')
ax.text(14.5, y_out+0.85, 'Deploy to 100%', fontsize=11, ha='center', color='white')
ax.text(14.5, y_out+0.5, 'High Quality + High ROI', fontsize=9, ha='center')
ax.text(14.5, y_out+0.15, 'Full Production', fontsize=9, ha='center', style='italic')

# CANARY Box
canary_box = FancyBboxPatch((7, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                            edgecolor=c_canary, facecolor=c_canary, alpha=0.4, linewidth=3)
ax.add_patch(canary_box)
ax.text(9, y_out+1.25, '⚠ CANARY', fontsize=16, fontweight='bold', ha='center', color='white')
ax.text(9, y_out+0.85, 'Test on 10-20%', fontsize=11, ha='center', color='white')
ax.text(9, y_out+0.5, 'Medium Quality / ROI', fontsize=9, ha='center')
ax.text(9, y_out+0.15, 'Gradual Rollout', fontsize=9, ha='center', style='italic')

# HOLD Box
hold_box = FancyBboxPatch((1.5, y_out), 4, 1.6, boxstyle="round,pad=0.15",
                          edgecolor=c_hold, facecolor=c_hold, alpha=0.4, linewidth=3)
ax.add_patch(hold_box)
ax.text(3.5, y_out+1.25, '✗ HOLD', fontsize=16, fontweight='bold', ha='center', color='white')
ax.text(3.5, y_out+0.85, 'Do NOT Deploy', fontsize=11, ha='center', color='white')
ax.text(3.5, y_out+0.5, 'Low Quality / High Risk', fontsize=9, ha='center')
ax.text(3.5, y_out+0.15, 'Re-design needed', fontsize=9, ha='center', style='italic')

# === Detailed Criteria Box ===
criteria_box = FancyBboxPatch((0.5, 0.3), 17, 2.8, boxstyle="round,pad=0.15",
                              edgecolor='gray', facecolor='#F5F5F5', alpha=0.9, linewidth=2)
ax.add_patch(criteria_box)
ax.text(9, 2.9, 'Detailed Decision Criteria', fontsize=13, fontweight='bold', ha='center')

# GO Criteria
ax.text(1, 2.5, 'GO Criteria:', fontsize=10, fontweight='bold', color=c_go)
go_criteria = [
    '• CAS ≥ 0.8 (High causal confidence)',
    '• ROI > 1.5 (Strong profitability)',
    '• CVaR within acceptable range',
    '• Balance SMD < 0.1',
    '• Overlap check passed',
    '• Sample size > min threshold'
]
for i, crit in enumerate(go_criteria):
    ax.text(1.2, 2.2 - i*0.25, crit, fontsize=8)

# CANARY Criteria
ax.text(7, 2.5, 'CANARY Criteria:', fontsize=10, fontweight='bold', color=c_canary)
canary_criteria = [
    '• 0.6 ≤ CAS < 0.8 (Medium confidence)',
    '• ROI > 1.0 but ≤ 1.5',
    '• Moderate risk (CVaR acceptable)',
    '• Some diagnostic warnings',
    '• Requires monitoring',
    '• Test on small segment first'
]
for i, crit in enumerate(canary_criteria):
    ax.text(7.2, 2.2 - i*0.25, crit, fontsize=8)

# HOLD Criteria
ax.text(13, 2.5, 'HOLD Criteria:', fontsize=10, fontweight='bold', color=c_hold)
hold_criteria = [
    '• CAS < 0.6 (Low confidence)',
    '• ROI ≤ 1.0 or negative Δ¥',
    '• High CVaR (unacceptable risk)',
    '• Failed balance/overlap checks',
    '• Sensitivity tests failed',
    '• Governance violations'
]
for i, crit in enumerate(hold_criteria):
    ax.text(13.2, 2.2 - i*0.25, crit, fontsize=8)

# Footer note
ax.text(9, 0.1, 'Note: All decisions are logged with full audit trail for compliance and reproducibility',
        fontsize=8, ha='center', style='italic', color='gray',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.5))

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/decision_flow_logic.png', dpi=300, bbox_inches='tight')
print("✓ Decision Flow Logic diagram created: Picture/decision_flow_logic.png")
