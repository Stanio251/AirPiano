import mido
import time

# Open a virtual MIDI output port (can be connected to DAW or synth)
try:
    outport = mido.open_output('Python MIDI Out', virtual=True)
except:
    # Fallback if virtual port fails (e.g., on Windows)
    outport = mido.open_output()

def play(note, strength):
    """
    Plays a MIDI note with given pitch (note) and velocity (strength).
    
    Parameters:
    - note: int (0-127) MIDI note number
    - strength: int (0-127) velocity
    """
    msg_on = mido.Message('note_on', note=note, velocity=strength)
    msg_off = mido.Message('note_off', note=note, velocity=strength)

    outport.send(msg_on)
    print(f"Note on: {note}")
    time.sleep(0.5)

    outport.send(msg_off)
    print(f"Note off: {note}")
    time.sleep(0.1)

# Optional test
if __name__ == "__main__":
    print("Testing note C4 (60)...")
    play(60, 100)
