import storage
import board
import digitalio

# Self-update (OTA) toggle jumper pin: GP22
# If GP22 is connected to GND (jumper installed), the Mac can write to the drive (safe mode for editing code).
# If GP22 is open (jumper removed), the Pico W itself can write to its drive (enables self-update/OTA downloads).
jumper = digitalio.DigitalInOut(board.GP22)
jumper.direction = digitalio.Direction.INPUT
jumper.pull = digitalio.Pull.UP

# If jumper.value is True (pin high, no jumper), the Pico W gets write access (OTA Mode).
# If jumper.value is False (pin low, connected to GND), the Mac gets write access (USB Dev Mode).
# Always mount the filesystem as writable for development
print("Boot: Mounting CIRCUITPY as writable (no jumper needed).")
storage.remount("/", readonly=False)

# Optional: log free RAM at boot (useful for debugging low‑memory issues)
try:
    import gc
    free = gc.mem_free()
    print(f"Free RAM at boot: {free} bytes")
except Exception as e:
    print(f"RAM diagnostic unavailable: {e}")

