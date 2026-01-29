"""
Generate simple sound effects for the Family Feud game.
This script creates basic WAV files for game sounds.
For better quality, replace these with professional sound effects.
"""

import wave
import math
import struct


def generate_beep(filename, frequency, duration, volume=0.5):
    """
    Generate a simple beep sound.

    Args:
        filename: Output file path
        frequency: Frequency in Hz
        duration: Duration in seconds
        volume: Volume (0.0 to 1.0)
    """
    sample_rate = 44100
    num_samples = int(sample_rate * duration)

    wav_file = wave.open(filename, 'w')
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)

    for i in range(num_samples):
        # Generate sine wave
        value = int(volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        data = struct.pack('<h', value)
        wav_file.writeframesraw(data)

    wav_file.close()
    print(f"[OK] Generated {filename}")


def generate_ding():
    """Generate a 'ding' sound for correct answers (high pitch, short)."""
    generate_beep('static/sounds/ding.mp3', 800, 0.3, 0.6)


def generate_buzzer():
    """Generate a 'buzzer' sound for wrong answers (low pitch, longer)."""
    generate_beep('static/sounds/buzzer.mp3', 200, 0.5, 0.7)


def generate_strike():
    """Generate a 'strike' sound (descending tone)."""
    sample_rate = 44100
    duration = 0.4
    num_samples = int(sample_rate * duration)

    wav_file = wave.open('static/sounds/strike.mp3', 'w')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)

    start_freq = 400
    end_freq = 150

    for i in range(num_samples):
        # Descending frequency
        progress = i / num_samples
        frequency = start_freq - (start_freq - end_freq) * progress
        value = int(0.6 * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        data = struct.pack('<h', value)
        wav_file.writeframesraw(data)

    wav_file.close()
    print("[OK] Generated static/sounds/strike.mp3")


if __name__ == '__main__':
    print("=" * 50)
    print("Generating sound effects...")
    print("=" * 50)

    generate_ding()
    generate_buzzer()
    generate_strike()

    print("\n[OK] All sounds generated successfully!")
    print("\nNote: These are basic sound effects.")
    print("For better quality, you can download free sounds from:")
    print("- https://freesound.org/")
    print("- https://mixkit.co/free-sound-effects/")
    print("=" * 50)
