"""
Common configuration for all CQOx diagrams
- Dark theme colors
- Larger font sizes
- Japanese font support
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# === Font Configuration ===
def setup_japanese_font():
    """Setup Japanese font and return FontProperties object"""
    # Try multiple Japanese font paths
    font_paths = [
        '/usr/share/fonts/google-droid-sans-fonts/DroidSansJapanese.ttf',
        '/usr/share/fonts/haranoaji/HaranoAjiGothic-Regular.otf',
        '/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf'
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                japanese_font = fm.FontProperties(fname=font_path)
                print(f"✓ Using Japanese font: {font_path}")
                return japanese_font
            except Exception as e:
                print(f"✗ Failed to load {font_path}: {e}")
                continue

    print("⚠ No Japanese font found, using default")
    return None

# === Color Schemes (Dark Theme) ===
DARK_THEME = {
    'background': '#1E1E23',      # Dark background
    'text': '#E0E0E5',            # Light gray text
    'text_secondary': '#B0B0B5',  # Secondary text
    'accent_blue': '#4A9EFF',     # Bright blue
    'accent_green': '#50E3A6',    # Bright green
    'accent_orange': '#FFB84D',   # Bright orange
    'accent_red': '#FF6B6B',      # Bright red
    'accent_purple': '#B794F6',   # Bright purple
    'accent_yellow': '#FFD93D',   # Bright yellow
    'box_data': '#2D5A7B',        # Dark blue for data
    'box_causal': '#6B4F9E',      # Dark purple for causal
    'box_decision': '#3D7A5C',    # Dark green for decision
    'box_governance': '#8B4A4A',  # Dark red for governance
    'box_export': '#9E7B3D',      # Dark orange for export
}

# === Font Sizes (Increased 40-50%) ===
FONT_SIZES = {
    'title': 30,          # Main title (was 20-24)
    'subtitle': 16,       # Subtitle (was 11-14)
    'heading': 18,        # Section headings (was 12-14)
    'label': 14,          # Box labels (was 9-11)
    'body': 12,           # Body text (was 8-9)
    'detail': 10,         # Detail text (was 7-8)
}

def setup_dark_theme(fig, ax):
    """Apply dark theme to figure and axes"""
    fig.patch.set_facecolor(DARK_THEME['background'])
    ax.set_facecolor(DARK_THEME['background'])
    plt.rcParams['text.color'] = DARK_THEME['text']
    plt.rcParams['axes.labelcolor'] = DARK_THEME['text']
    plt.rcParams['xtick.color'] = DARK_THEME['text']
    plt.rcParams['ytick.color'] = DARK_THEME['text']
    plt.rcParams['axes.unicode_minus'] = False

def get_text_kwargs(japanese_font=None, size='body', color=None, weight='normal'):
    """Get consistent text styling kwargs

    Note: Only use japanese_font parameter for text that contains Japanese characters.
    English-only text should NOT use japanese_font to avoid glyph warnings.
    """
    kwargs = {
        'fontsize': FONT_SIZES[size],
        'color': color if color else DARK_THEME['text'],
        'fontweight': weight
    }
    if japanese_font:
        kwargs['fontproperties'] = japanese_font
    return kwargs

def has_japanese(text):
    """Check if text contains Japanese characters"""
    if not text:
        return False
    for char in text:
        if ord(char) > 0x3000:  # Japanese characters start from U+3000
            return True
    return False
