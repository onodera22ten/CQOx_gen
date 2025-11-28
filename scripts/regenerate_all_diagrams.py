"""
Regenerate all CQOx diagrams with:
- Dark theme background
- Larger font sizes
- Proper Japanese font support
"""

import subprocess
import os

# Set matplotlib backend to non-interactive
os.environ['MPLBACKEND'] = 'Agg'

scripts_to_run = [
    '/home/hirokionodera/CQOx_gen/visualizations/create_user_journey_v2.py',
    '/home/hirokionodera/CQOx_gen/visualizations/create_causal_workflow_v2.py',
    '/home/hirokionodera/CQOx_gen/visualizations/create_decision_flow_v2.py',
    '/home/hirokionodera/CQOx_gen/visualizations/create_system_architecture_v2.py'
]

print("=== Regenerating All Diagrams with Dark Theme + Japanese Fonts ===\n")

for script in scripts_to_run:
    script_name = os.path.basename(script)
    print(f"Running: {script_name}")

    try:
        result = subprocess.run(
            ['python3', script],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"✓ {script_name} completed")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()}")
        else:
            print(f"✗ {script_name} failed")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        print(f"✗ {script_name} timed out")
    except Exception as e:
        print(f"✗ {script_name} error: {e}")

    print()

print("=== All diagrams regenerated ===")
