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
if jumper.value:
    print("OTA Mode: Pico W has write access to filesystem. Mac USB writing disabled.")
    storage.remount("/", readonly=False)
else:
    print("USB Dev Mode: Mac has write access. Pico W code cannot write to filesystem.")
    storage.remount("/", readonly=True)

