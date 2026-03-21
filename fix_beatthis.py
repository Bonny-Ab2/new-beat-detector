import os
import re

# Path to beat_this package
beatthis_path = '.venv/lib/python3.9/site-packages/beat_this'
if not os.path.exists(beatthis_path):
    beatthis_path = 'venv39/lib/python3.9/site-packages/beat_this'

for root, dirs, files in os.walk(beatthis_path):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Fix variable annotations
            content = re.sub(r':\s*([A-Za-z_\.]+)\s*\|\s*None', r': Optional[\1]', content)
            
            # Fix function signatures
            content = re.sub(r'->\s*([A-Za-z_\.]+)\s*\|\s*None', r'-> Optional[\1]', content)
            content = re.sub(r'([a-z_]+):\s*([A-Za-z_\.]+)\s*\|\s*([A-Za-z_\.]+)', r'\1: Union[\2, \3]', content)
            
            # Add imports if needed
            if 'from typing import Optional, Union' not in content:
                if 'Optional' in content or 'Union' in content:
                    if 'from torch import nn' in content:
                        content = content.replace('from torch import nn', 'from typing import Optional, Union\nfrom torch import nn')
                    elif 'import torch' in content:
                        content = content.replace('import torch', 'from typing import Optional, Union\nimport torch')
            
            with open(filepath, 'w') as f:
                f.write(content)
                print(f'Fixed: {filepath}')
