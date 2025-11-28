"""
CQOx User Journey Visualization - Dark Theme with Japanese Font Support
Creates a comprehensive flow diagram showing the end-to-end journey from data upload to export
Based on CQOx.PDF workflow
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines
from diagram_config import setup_japanese_font, DARK_THEME, FONT_SIZES, setup_dark_theme, get_text_kwargs
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Setup Japanese font
japanese_font = setup_japanese_font()

# Set up the figure with larger size
fig, ax = plt.subplots(1, 1, figsize=(24, 16))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Apply dark theme
setup_dark_theme(fig, ax)

# Title
ax.text(5, 9.5, 'CQOx User Journey: From CSV Upload to Action',
        **get_text_kwargs(japanese_font, 'title', weight='bold'), ha='center', va='top')
ax.text(5, 9.1, 'データアップロード → 因果推論 → 意思決定 → ガバナンス → エクスポート',
        **get_text_kwargs(japanese_font, 'subtitle', DARK_THEME['text_secondary']),
        ha='center', va='top', style='italic')

# Phase labels
ax.text(2.0, 8.95, 'Phase 1: Data Ingestion', **get_text_kwargs(None, 'detail', DARK_THEME['accent_blue']),
        ha='center', bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_data'], alpha=0.3, edgecolor=DARK_THEME['accent_blue']))
ax.text(5.5, 8.95, 'Phase 2: Causal Analysis', **get_text_kwargs(None, 'detail', DARK_THEME['accent_purple']),
        ha='center', bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_causal'], alpha=0.3, edgecolor=DARK_THEME['accent_purple']))

# Step 1: Datasets (データを持ち込む)
y_start = 8.0
box1 = FancyBboxPatch((0.2, y_start), 1.8, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'], alpha=0.4, linewidth=2.5)
ax.add_patch(box1)
ax.text(1.1, y_start+0.65, '① Datasets', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(1.1, y_start+0.40, 'データを持ち込む', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(1.1, y_start+0.08, '• CSV Upload\n• Schema Detection\n• Basic Statistics',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Arrow 1->2
arrow1 = FancyArrowPatch((2.1, y_start+0.45), (2.8, y_start+0.45),
                         arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow1)

# Step 2: Causal Design (因果の設計図をつくる)
box2 = FancyBboxPatch((2.9, y_start), 1.8, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_purple'], facecolor=DARK_THEME['box_causal'], alpha=0.4, linewidth=2.5)
ax.add_patch(box2)
ax.text(3.8, y_start+0.65, '② Causal Design', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(3.8, y_start+0.40, '因果の設計図をつくる', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(3.8, y_start+0.08, '• Treatment/Outcome\n• Estimator Selection\n• Train Models',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Arrow 2->3
arrow2 = FancyArrowPatch((4.8, y_start+0.45), (5.5, y_start+0.45),
                         arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow2)

# Step 3: Diagnostics (因果推論と診断)
box3 = FancyBboxPatch((5.6, y_start), 1.8, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_purple'], facecolor=DARK_THEME['box_causal'], alpha=0.4, linewidth=2.5)
ax.add_patch(box3)
ax.text(6.5, y_start+0.65, '③ Diagnostics', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(6.5, y_start+0.40, '因果推論と診断', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(6.5, y_start+0.08, '• Δ¥ Estimation\n• Balance/Overlap\n• CAS Score',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Arrow 3->4
arrow3 = FancyArrowPatch((7.5, y_start+0.45), (8.2, y_start+0.45),
                         arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow3)

# Step 4: Policies (施策単位の結果を整理)
box4 = FancyBboxPatch((8.3, y_start), 1.5, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'], alpha=0.4, linewidth=2.5)
ax.add_patch(box4)
ax.text(9.05, y_start+0.65, '④ Policies', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(9.05, y_start+0.40, '施策整理', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(9.05, y_start+0.08, '• Policy Cards\n• Δ¥/ROI/Risk\n• GO/CANARY/HOLD',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Role label (Analyst)
ax.text(9.8, y_start+0.45, 'Analyst\nアナリスト', **get_text_kwargs(japanese_font, 'detail'),
        ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_causal'], alpha=0.5, edgecolor=DARK_THEME['accent_purple']))

# Downward arrow from Policies
arrow4_down = FancyArrowPatch((9.05, y_start-0.05), (9.05, 6.95),
                              arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow4_down)

# Phase 3 label
ax.text(5.0, 7.15, 'Phase 3: Executive Decision', **get_text_kwargs(None, 'detail', DARK_THEME['accent_green']),
        ha='center', bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_decision'], alpha=0.3, edgecolor=DARK_THEME['accent_green']))

# Step 5: Decision Console (一枚で経営判断)
y_middle = 6.4
box5 = FancyBboxPatch((7.5, y_middle), 2.3, 0.95, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'], alpha=0.4, linewidth=2.5)
ax.add_patch(box5)
ax.text(8.65, y_middle+0.72, '⑤ Decision Console', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(8.65, y_middle+0.48, '一枚で経営判断', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(8.65, y_middle+0.08, '• Total Δ¥\n• Mean CAS / CVaR\n• Decision Cards Table',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Role label (CMO/Manager)
ax.text(9.8, y_middle+0.48, 'CMO/Manager\n経営・マーケ', **get_text_kwargs(japanese_font, 'detail'),
        ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_decision'], alpha=0.5, edgecolor=DARK_THEME['accent_green']))

# Leftward arrow to Portfolio
arrow5_left = FancyArrowPatch((7.4, y_middle+0.48), (5.3, y_middle+0.48),
                              arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow5_left)

# Step 6: Portfolio (施策の組み合わせ)
box6 = FancyBboxPatch((2.7, y_middle), 2.5, 0.95, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'], alpha=0.4, linewidth=2.5)
ax.add_patch(box6)
ax.text(3.95, y_middle+0.72, '⑥ Portfolio & ROI', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(3.95, y_middle+0.48, 'どの施策を組み合わせるか', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(3.95, y_middle+0.08, '• Pareto Frontier\n• Include/Test/Exclude\n• Budget Optimization',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Leftward arrow to Digital Twin
arrow6_left = FancyArrowPatch((2.6, y_middle+0.48), (2.1, y_middle+0.48),
                              arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow6_left)

# Step 7: Digital Twin (事前に未来を試す)
box7 = FancyBboxPatch((0.1, y_middle), 1.9, 0.95, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'], alpha=0.4, linewidth=2.5)
ax.add_patch(box7)
ax.text(1.05, y_middle+0.72, '⑦ Digital Twin', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(1.05, y_middle+0.48, '事前に未来を試す', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(1.05, y_middle+0.08, '• Persona Cards\n• Scenario Simulation\n• Pre-deployment Test',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Downward arrow from Digital Twin
arrow7_down = FancyArrowPatch((1.05, y_middle-0.05), (1.05, 5.3),
                              arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow7_down)

# Phase 4 label
ax.text(2.5, 5.5, 'Phase 4: Governance & Export', **get_text_kwargs(None, 'detail', DARK_THEME['accent_red']),
        ha='center', bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_governance'], alpha=0.3, edgecolor=DARK_THEME['accent_red']))

# Step 8a: Experiment Studio (実験管理)
y_lower = 4.2
box8a = FancyBboxPatch((0.1, y_lower), 1.9, 0.95, boxstyle="round,pad=0.1",
                        edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'], alpha=0.4, linewidth=2.5)
ax.add_patch(box8a)
ax.text(1.05, y_lower+0.72, '⑧a Experiment Studio', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(1.05, y_lower+0.48, '実験管理', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(1.05, y_lower+0.08, '• A/B Test Setup\n• Multi-Arm Bandit\n• Online/Offline',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Step 8b: Governance Center (ガバナンス)
box8b = FancyBboxPatch((2.5, y_lower), 2.0, 0.95, boxstyle="round,pad=0.1",
                        edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'], alpha=0.4, linewidth=2.5)
ax.add_patch(box8b)
ax.text(3.5, y_lower+0.72, '⑧b Governance Center', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(3.5, y_lower+0.48, 'ガバナンスチェック', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(3.5, y_lower+0.08, '• Fairness Check\n• Data Quality\n• Frequency Cap',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Role label (Compliance)
ax.text(9.8, y_lower+0.48, 'Compliance\nガバナンス', **get_text_kwargs(japanese_font, 'detail'),
        ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor=DARK_THEME['box_governance'], alpha=0.5, edgecolor=DARK_THEME['accent_red']))

# Arrow from Experiment Studio to Governance
arrow8 = FancyArrowPatch((2.1, y_lower+0.48), (2.4, y_lower+0.48),
                         arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow8)

# Arrow from Governance to Export
arrow9 = FancyArrowPatch((4.6, y_lower+0.48), (6.2, y_lower+0.48),
                         arrowstyle='->', mutation_scale=25, linewidth=3, color=DARK_THEME['text'])
ax.add_patch(arrow9)

# Step 9: Export Gate (配信システムへ渡す)
box9 = FancyBboxPatch((6.3, y_lower), 3.5, 0.95, boxstyle="round,pad=0.1",
                       edgecolor=DARK_THEME['accent_orange'], facecolor=DARK_THEME['box_export'], alpha=0.4, linewidth=2.5)
ax.add_patch(box9)
ax.text(8.05, y_lower+0.72, '⑨ Export Gate', **get_text_kwargs(japanese_font, 'label', weight='bold'), ha='center')
ax.text(8.05, y_lower+0.48, '配信システムへ渡す', **get_text_kwargs(japanese_font, 'body'), ha='center', style='italic')
ax.text(8.05, y_lower+0.08, '• Policy ID + Segment Definition\n• Budget/Frequency Limits\n• JSON/CSV → MA Tools (KARTE, etc.)',
        **get_text_kwargs(None, 'detail'), ha='center', va='bottom')

# Add key insight box at bottom
insight_text = """Key Insight: CQOxはバラバラな機能ではなく、一本のストーリー
「どの施策を、誰に、どれだけやるか」を、データから配信まで一気通貫で決めるシステム"""

ax.text(5, 2.9, insight_text, **get_text_kwargs(japanese_font, 'body', DARK_THEME['text'], 'bold'), ha='center', va='top',
        bbox=dict(boxstyle='round,pad=0.8', facecolor=DARK_THEME['accent_yellow'], alpha=0.3,
                  edgecolor=DARK_THEME['accent_yellow'], linewidth=3))

# Legend
legend_elements = [
    mpatches.Patch(facecolor=DARK_THEME['box_data'], alpha=0.4, edgecolor=DARK_THEME['accent_blue'], label='Data Stage'),
    mpatches.Patch(facecolor=DARK_THEME['box_causal'], alpha=0.4, edgecolor=DARK_THEME['accent_purple'], label='Causal Analysis'),
    mpatches.Patch(facecolor=DARK_THEME['box_decision'], alpha=0.4, edgecolor=DARK_THEME['accent_green'], label='Decision Making'),
    mpatches.Patch(facecolor=DARK_THEME['box_governance'], alpha=0.4, edgecolor=DARK_THEME['accent_red'], label='Governance'),
    mpatches.Patch(facecolor=DARK_THEME['box_export'], alpha=0.4, edgecolor=DARK_THEME['accent_orange'], label='Export')
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=FONT_SIZES['body'], framealpha=0.9,
          facecolor=DARK_THEME['background'], edgecolor=DARK_THEME['text'], labelcolor=DARK_THEME['text'])

# Add timestamp
ax.text(0.1, 0.1, 'Generated by CQOx Documentation System', **get_text_kwargs(None, 'detail', DARK_THEME['text_secondary']),
        style='italic')

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/user_journey_flow.png', dpi=300, bbox_inches='tight', facecolor=DARK_THEME['background'])
print("✓ User Journey flow diagram created: Picture/user_journey_flow.png")
