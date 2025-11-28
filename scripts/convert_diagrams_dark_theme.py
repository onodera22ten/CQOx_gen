"""
Convert CQOx diagram images to dark theme - FAST vectorized version
"""

from PIL import Image
import numpy as np
import os

# Paths
PICTURE_DIR = "/home/hirokionodera/CQOx_gen/Picture"

# Files to convert
DIAGRAMS = [
    "causal_inference_workflow.png",
    "decision_flow_logic.png",
    "system_architecture.png",
    "user_journey_flow.png"
]

def convert_to_dark_theme(input_path, output_path):
    """
    Convert an image to dark theme using fast NumPy vectorized operations
    """
    print(f"Converting: {input_path}")

    # Load image and convert to numpy array
    img = Image.open(input_path)
    img_array = np.array(img, dtype=np.float32)

    # Separate RGB channels (ignore alpha if present)
    if img_array.shape[2] == 4:  # RGBA
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3:4]
    else:  # RGB
        rgb = img_array
        alpha = None

    # Calculate brightness for each pixel
    brightness = (rgb[:, :, 0] + rgb[:, :, 1] + rgb[:, :, 2]) / 3.0

    # Create mask for very light pixels (white/near-white backgrounds)
    very_light_mask = (brightness > 240).astype(np.float32)
    very_light_mask = very_light_mask[:, :, np.newaxis]  # Add channel dimension

    # Create mask for light pixels (light colored elements)
    light_mask = ((brightness > 180) & (brightness <= 240)).astype(np.float32)
    light_mask = light_mask[:, :, np.newaxis]

    # Create mask for dark pixels (text and lines)
    dark_mask = (brightness < 80).astype(np.float32)
    dark_mask = dark_mask[:, :, np.newaxis]

    # Create output array
    output = np.zeros_like(rgb)

    # Convert very light pixels to dark background
    output += very_light_mask * np.array([30, 30, 35])

    # Convert light colored elements to darker versions (reduce brightness)
    light_pixels = rgb * light_mask
    # Darken by factor of 0.4 and shift hue slightly
    darkened_light = light_pixels * 0.4 + np.array([20, 20, 25]) * light_mask
    output += darkened_light

    # Convert dark pixels to light (for text)
    output += dark_mask * np.array([220, 220, 225])

    # Medium brightness pixels (keep relatively unchanged but slightly adjusted)
    medium_mask = 1.0 - (very_light_mask + light_mask + dark_mask)
    medium_pixels = rgb * medium_mask
    # Slightly darken medium tones
    output += medium_pixels * 0.7

    # Clip values to valid range
    output = np.clip(output, 0, 255).astype(np.uint8)

    # Recombine with alpha channel if it exists
    if alpha is not None:
        output = np.concatenate([output, alpha.astype(np.uint8)], axis=2)

    # Convert back to PIL Image
    result_img = Image.fromarray(output)

    # Save
    result_img.save(output_path, 'PNG', optimize=True)
    print(f"✓ Saved: {output_path}")

def main():
    print("=== Converting Diagrams to Dark Theme ===\n")

    for diagram in DIAGRAMS:
        input_path = os.path.join(PICTURE_DIR, diagram)

        # Check if file exists
        if not os.path.exists(input_path):
            print(f"✗ File not found: {input_path}")
            continue

        # Create backup
        backup_path = input_path.replace('.png', '_light_backup.png')
        if not os.path.exists(backup_path):
            img = Image.open(input_path)
            img.save(backup_path)
            print(f"✓ Backup created: {backup_path}")

        # Convert to dark theme
        output_path = input_path.replace('.png', '_dark.png')
        convert_to_dark_theme(input_path, output_path)

    print("\n=== Conversion Complete ===")
    print("Original images backed up with '_light_backup.png' suffix")
    print("Dark theme images saved with '_dark.png' suffix")

if __name__ == "__main__":
    main()
