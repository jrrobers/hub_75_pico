# memory_guard.py
"""Utility to monitor free RAM on a CircuitPython device.
Provides a simple check that can be called at startup or before memory‑intensive operations.
"""
import gc

def check_memory(min_free_bytes: int = 8000) -> None:
    """Print a warning if free RAM falls below *min_free_bytes*.
    Args:
        min_free_bytes: Threshold in bytes. Default is 8000 (≈8 KB).
    """
    try:
        free = gc.mem_free()
        total = gc.mem_alloc() + free
        print(f"[Memory Guard] Free RAM: {free} bytes (Total: {total} bytes)")
        if free < min_free_bytes:
            print(
                f"[Memory Guard] WARNING: Low memory! Less than {min_free_bytes} bytes free. "
                "Consider reducing data structures or delaying heavy work."
            )
    except Exception as e:
        print(f"[Memory Guard] Unable to check RAM: {e}")
