import sys; sys.modules['pyaudio'] = __import__('types').ModuleType('pyaudio'); from BeatNet.BeatNet import BeatNet; print('Success')
