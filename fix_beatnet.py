import sys
import types

# Create mock for madmom._internal
mock_internal = types.ModuleType('madmom._internal')
sys.modules['madmom._internal'] = mock_internal

# Also mock madmom if needed
if 'madmom' not in sys.modules:
    sys.modules['madmom'] = types.ModuleType('madmom')
