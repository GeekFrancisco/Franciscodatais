
import moviepy.audio.fx as afx
import inspect

print("Audio FX contents:")
for name, obj in inspect.getmembers(afx):
    print(name)

try:
    from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
    print("\nMultiplyVolume found!")
except ImportError:
    print("\nMultiplyVolume NOT found.")
