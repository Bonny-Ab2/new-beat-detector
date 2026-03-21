import os
import re

beatthis_path = '.venv/lib/python3.9/site-packages/beat_this'
if not os.path.exists(beatthis_path):
    beatthis_path = 'venv39/lib/python3.9/site-packages/beat_this'

for root, dirs, files in os.walk(beatthis_path):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Fix union types
            content = re.sub(r': ([A-Za-z_\.]+) \| None', r': Optional[\1]', content)
            content = re.sub(r'([a-z_]+): ([A-Za-z_\.]+) \| None', r'\1: Optional[\2]', content)
            
            # Add import if needed
            if 'from typing import Optional' not in content and 'Optional' in content:
                content = content.replace('from torch import nn', 'from typing import Optional\nfrom torch import nn')
                content = content.replace('import torch', 'from typing import Optional\nimport torch')
            
            with open(filepath, 'w') as f:
                f.write(content)
                print(f'Fixed: {filepath}')
