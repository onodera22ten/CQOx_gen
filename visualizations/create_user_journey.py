"""
CQOx User Journey Visualization
Creates a comprehensive flow diagram showing the end-to-end journey from data upload to export
Based on CQOx.PDF workflow
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines
import matplotlib.font_manager as fm
import os
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Set Japanese font - find available Japanese fonts
japanese_font = None
font_names_to_try = [
    'Noto Sans CJK JP',
    'Noto Sans Mono CJK JP',
    'Droid Sans Japanese',
    'Harano Aji Gothic'
]

# Try to find font by name first
for font_name in font_names_to_try:
    try:
        # Get font file path
        font_files = [f for f in fm.fontManager.ttflist if font_name in f.name]
        if font_files:
            # Use TTF/OTF files, avoid TTC if possible
            ttf_fonts = [f for f in font_files if f.fname.endswith(('.ttf', '.otf'))]
            if ttf_fonts:
                font_file = ttf_fonts[0].fname
                japanese_font = fm.FontProperties(fname=font_file)
                print(f"Using Japanese font: {font_name} from {font_file}")
                break
            elif font_files:
                # Fallback to first available
                japanese_font = fm.FontProperties(family=font_name)
                print(f"Using Japanese font by name: {font_name}")
                break
    except Exception as e:
        continue

# If still not found, try Droid Sans Japanese TTF directly
if not japanese_font:
    droid_path = '/usr/share/fonts/google-droid-sans-fonts/DroidSansJapanese.ttf'
    if os.path.exists(droid_path):
        try:
            japanese_font = fm.FontProperties(fname=droid_path)
            print(f"Using Japanese font: Droid Sans Japanese from {droid_path}")
        except:
            pass

# Final fallback: try Harano Aji Gothic
if not japanese_font:
    harano_path = '/usr/share/fonts/haranoaji/HaranoAjiGothic-Regular.otf'
    if os.path.exists(harano_path):
        try:
            japanese_font = fm.FontProperties(fname=harano_path)
            print(f"Using Japanese font: Harano Aji Gothic from {harano_path}")
        except:
            pass

# Do not set default font globally - apply only to Japanese text via fontproperties

plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors
color_data = '#4A90E2'      # Blue for data stages
color_causal = '#7B68EE'    # Purple for causal analysis
color_decision = '#50C878'  # Green for decision stages
color_governance = '#FF6B6B'  # Red for governance
color_export = '#FFA500'    # Orange for export

# Title
ax.text(5, 9.5, 'CQOx User Journey: From CSV Upload to Action',
        fontsize=24, fontweight='bold', ha='center', va='top')
ax.text(5, 9.1, 'データアップロード → 因果推論 → 意思決定 → ガバナンス → エクスポート',
        fontsize=14, ha='center', va='top', style='italic', color='gray',
        fontproperties=japanese_font if japanese_font else None)

# Step 1: Datasets (データを持ち込む)
y_start = 8.0
box1 = FancyBboxPatch((0.2, y_start), 1.8, 0.8, boxstyle="round,pad=0.1",
                       edgecolor=color_data, facecolor=color_data, alpha=0.3, linewidth=2)
ax.add_patch(box1)
ax.text(1.1, y_start+0.6, '① Datasets', fontsize=14, fontweight='bold', ha='center')
ax.text(1.1, y_start+0.35, 'データを持ち込む', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(1.1, y_start+0.05, '• CSV Upload\n• Schema Detection\n• Basic Statistics',
        fontsize=8, ha='center', va='bottom')

# Arrow 1->2
arrow1 = FancyArrowPatch((2.1, y_start+0.4), (2.8, y_start+0.4),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow1)

# Step 2: Causal Design (因果の設計図をつくる)
box2 = FancyBboxPatch((2.9, y_start), 1.8, 0.8, boxstyle="round,pad=0.1",
                       edgecolor=color_causal, facecolor=color_causal, alpha=0.3, linewidth=2)
ax.add_patch(box2)
ax.text(3.8, y_start+0.6, '② Causal Design', fontsize=14, fontweight='bold', ha='center')
ax.text(3.8, y_start+0.35, '因果の設計図をつくる', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(3.8, y_start+0.05, '• Treatment/Outcome\n• Estimator Selection\n• Train Models',
        fontsize=8, ha='center', va='bottom')

# Arrow 2->3
arrow2 = FancyArrowPatch((4.8, y_start+0.4), (5.5, y_start+0.4),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow2)

# Step 3: Diagnostics (因果推論と診断)
box3 = FancyBboxPatch((5.6, y_start), 1.8, 0.8, boxstyle="round,pad=0.1",
                       edgecolor=color_causal, facecolor=color_causal, alpha=0.3, linewidth=2)
ax.add_patch(box3)
ax.text(6.5, y_start+0.6, '③ Diagnostics', fontsize=14, fontweight='bold', ha='center')
ax.text(6.5, y_start+0.35, '因果推論と診断', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(6.5, y_start+0.05, '• Δ¥ Estimation\n• Balance/Overlap\n• CAS Score',
        fontsize=8, ha='center', va='bottom')

# Arrow 3->4
arrow3 = FancyArrowPatch((7.5, y_start+0.4), (8.2, y_start+0.4),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow3)

# Step 4: Policies (施策単位の結果を整理)
box4 = FancyBboxPatch((8.3, y_start), 1.5, 0.8, boxstyle="round,pad=0.1",
                       edgecolor=color_decision, facecolor=color_decision, alpha=0.3, linewidth=2)
ax.add_patch(box4)
ax.text(9.05, y_start+0.6, '④ Policies', fontsize=14, fontweight='bold', ha='center')
ax.text(9.05, y_start+0.35, '施策整理', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(9.05, y_start+0.05, '• Policy Cards\n• Δ¥/ROI/Risk\n• GO/CANARY/HOLD',
        fontsize=8, ha='center', va='bottom')

# Downward arrow from Policies
arrow4_down = FancyArrowPatch((9.05, y_start-0.05), (9.05, y_start-0.6),
                              arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow4_down)

# Step 5: Decision Console (一枚で経営判断)
y_middle = 6.5
box5 = FancyBboxPatch((7.5, y_middle), 2.3, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=color_decision, facecolor=color_decision, alpha=0.3, linewidth=2)
ax.add_patch(box5)
ax.text(8.65, y_middle+0.7, '⑤ Decision Console', fontsize=14, fontweight='bold', ha='center')
ax.text(8.65, y_middle+0.45, '一枚で経営判断', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(8.65, y_middle+0.05, '• Total Δ¥\n• Mean CAS / CVaR\n• Decision Cards Table',
        fontsize=8, ha='center', va='bottom')

# Leftward arrow to Portfolio
arrow5_left = FancyArrowPatch((7.4, y_middle+0.45), (5.3, y_middle+0.45),
                              arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow5_left)

# Step 6: Portfolio (施策の組み合わせ)
box6 = FancyBboxPatch((2.7, y_middle), 2.5, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=color_decision, facecolor=color_decision, alpha=0.3, linewidth=2)
ax.add_patch(box6)
ax.text(3.95, y_middle+0.7, '⑥ Portfolio & ROI', fontsize=14, fontweight='bold', ha='center')
ax.text(3.95, y_middle+0.45, 'どの施策を組み合わせるか', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(3.95, y_middle+0.05, '• Pareto Frontier\n• Include/Test/Exclude\n• Budget Optimization',
        fontsize=8, ha='center', va='bottom')

# Leftward arrow to Digital Twin
arrow6_left = FancyArrowPatch((2.6, y_middle+0.45), (2.1, y_middle+0.45),
                              arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow6_left)

# Step 7: Digital Twin (事前に未来を試す)
box7 = FancyBboxPatch((0.1, y_middle), 1.9, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=color_decision, facecolor=color_decision, alpha=0.3, linewidth=2)
ax.add_patch(box7)
ax.text(1.05, y_middle+0.7, '⑦ Digital Twin', fontsize=14, fontweight='bold', ha='center')
ax.text(1.05, y_middle+0.45, '事前に未来を試す', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(1.05, y_middle+0.05, '• Persona Cards\n• Scenario Simulation\n• Pre-deployment Test',
        fontsize=8, ha='center', va='bottom')

# Downward arrow from Digital Twin
arrow7_down = FancyArrowPatch((1.05, y_middle-0.05), (1.05, 5.3),
                              arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow7_down)

# Step 8a: Experiment Studio (実運用の安全装置)
y_lower = 4.2
box8a = FancyBboxPatch((0.1, y_lower), 1.9, 0.9, boxstyle="round,pad=0.1",
                        edgecolor=color_governance, facecolor=color_governance, alpha=0.3, linewidth=2)
ax.add_patch(box8a)
ax.text(1.05, y_lower+0.7, '⑧a Experiment Studio', fontsize=13, fontweight='bold', ha='center')
ax.text(1.05, y_lower+0.45, '実験管理', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(1.05, y_lower+0.05, '• A/B Test Setup\n• Multi-Arm Bandit\n• Online/Offline',
        fontsize=8, ha='center', va='bottom')

# Step 8b: Governance Center (ガバナンス)
box8b = FancyBboxPatch((2.5, y_lower), 2.0, 0.9, boxstyle="round,pad=0.1",
                        edgecolor=color_governance, facecolor=color_governance, alpha=0.3, linewidth=2)
ax.add_patch(box8b)
ax.text(3.5, y_lower+0.7, '⑧b Governance Center', fontsize=13, fontweight='bold', ha='center')
ax.text(3.5, y_lower+0.45, 'ガバナンスチェック', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(3.5, y_lower+0.05, '• Fairness Check\n• Data Quality\n• Frequency Cap',
        fontsize=8, ha='center', va='bottom')

# Arrow from Experiment Studio to Governance
arrow8 = FancyArrowPatch((2.1, y_lower+0.45), (2.4, y_lower+0.45),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow8)

# Arrow from Governance to Export
arrow9 = FancyArrowPatch((4.6, y_lower+0.45), (6.2, y_lower+0.45),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='black')
ax.add_patch(arrow9)

# Step 9: Export Gate (配信システムへ渡す)
box9 = FancyBboxPatch((6.3, y_lower), 3.5, 0.9, boxstyle="round,pad=0.1",
                       edgecolor=color_export, facecolor=color_export, alpha=0.3, linewidth=2)
ax.add_patch(box9)
ax.text(8.05, y_lower+0.7, '⑨ Export Gate', fontsize=14, fontweight='bold', ha='center')
ax.text(8.05, y_lower+0.45, '配信システムへ渡す', fontsize=10, ha='center', style='italic',
        fontproperties=japanese_font if japanese_font else None)
ax.text(8.05, y_lower+0.05, '• Policy ID + Segment Definition\n• Budget/Frequency Limits\n• JSON/CSV → MA Tools (KARTE, etc.)',
        fontsize=8, ha='center', va='bottom')

# Add role labels on the right
ax.text(9.8, 8.4, 'Analyst\nアナリスト', fontsize=9, ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5),
        fontproperties=japanese_font if japanese_font else None)

ax.text(9.8, 6.95, 'CMO/Manager\n経営・マーケ', fontsize=9, ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5),
        fontproperties=japanese_font if japanese_font else None)

ax.text(9.8, 4.65, 'Compliance\nガバナンス', fontsize=9, ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5),
        fontproperties=japanese_font if japanese_font else None)

# Add key insight box at bottom
insight_text = """Key Insight: CQOxはバラバラな機能ではなく、一本のストーリー
「どの施策を、誰に、どれだけやるか」を、データから配信まで一気通貫で決めるシステム"""

ax.text(5, 2.8, insight_text, fontsize=11, ha='center', va='top',
        bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.3, edgecolor='black', linewidth=2),
        weight='bold', fontproperties=japanese_font if japanese_font else None)

# Add workflow phases
ax.text(2.0, 9.0, 'Phase 1: Data Ingestion', fontsize=10, ha='center',
        bbox=dict(boxstyle='round', facecolor=color_data, alpha=0.2))
ax.text(5.5, 9.0, 'Phase 2: Causal Analysis', fontsize=10, ha='center',
        bbox=dict(boxstyle='round', facecolor=color_causal, alpha=0.2))
ax.text(5.0, 7.2, 'Phase 3: Executive Decision', fontsize=10, ha='center',
        bbox=dict(boxstyle='round', facecolor=color_decision, alpha=0.2))
ax.text(2.5, 5.5, 'Phase 4: Governance & Export', fontsize=10, ha='center',
        bbox=dict(boxstyle='round', facecolor=color_governance, alpha=0.2))

# Legend
legend_elements = [
    mpatches.Patch(facecolor=color_data, alpha=0.3, edgecolor=color_data, label='Data Stage'),
    mpatches.Patch(facecolor=color_causal, alpha=0.3, edgecolor=color_causal, label='Causal Analysis'),
    mpatches.Patch(facecolor=color_decision, alpha=0.3, edgecolor=color_decision, label='Decision Making'),
    mpatches.Patch(facecolor=color_governance, alpha=0.3, edgecolor=color_governance, label='Governance'),
    mpatches.Patch(facecolor=color_export, alpha=0.3, edgecolor=color_export, label='Export')
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.9)

# Add timestamp
ax.text(0.1, 0.1, 'Generated by CQOx Documentation System', fontsize=8, style='italic', color='gray')

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/user_journey_flow.png', dpi=300, bbox_inches='tight')
print("✓ User Journey flow diagram created: Picture/user_journey_flow.png")
