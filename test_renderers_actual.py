#!/usr/bin/env python3
"""Test script to check actual renderer outputs."""

import sys

sys.path.insert(0, "src")

from shellpomodoro.display import make_renderer, Mode

# Test each renderer
test_payload = {
    "phase_label": "Focus",
    "i": 1,
    "n": 4,
    "remaining_s": 65,  # 01:05
    "elapsed_s": 35,  # 00:35
    "duration_s": 100,
    "progress": 0.35,
    "remaining_mmss": "01:05",
    "elapsed_mmss": "00:35",
}

print("=== Timer Back ===")
r = make_renderer(Mode.TIMER_BACK, None)
output = r.frame(test_payload)
print(f"Output: '{output}'")
print(f"Type: {type(output)}")
print()

print("=== Timer Forward ===")
r = make_renderer(Mode.TIMER_FWD, None)
output = r.frame(test_payload)
print(f"Output: '{output}'")
print(f"Type: {type(output)}")
print()

print("=== Bar ===")
r = make_renderer(Mode.BAR, None)
output = r.frame(test_payload)
print(f"Output: '{output}'")
print(f"Type: {type(output)}")
print()

print("=== Dots ===")
r = make_renderer(Mode.DOTS, 10)
output = r.frame(test_payload)
print(f"Output: '{output}'")
print(f"Type: {type(output)}")
print()

print("=== Dots at t=0 ===")
test_payload_t0 = {
    "phase_label": "Focus",
    "i": 1,
    "n": 4,
    "elapsed_s": 0,
    "duration_s": 100,
}
r = make_renderer(Mode.DOTS, 10)
output = r.frame(test_payload_t0)
print(f"Output: '{output}'")
print(f"Type: {type(output)}")
