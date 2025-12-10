import RPi.GPIO as GPIO
import time
import threading
import ollama
import sys

# ============================
# CONFIGURATION
# ============================

# Switch inputs (DIP)
SWITCH_PINS = {
    "sw1": 5,
    "sw2": 6,
    "sw3": 13,
    "sw4": 19,
    "sw5": 26,
    "sw6": 21
}

# LED outputs
LED_PINS = {
    "super_red": 17,
    "red": 27,
    "yellow": 22,
    "green": 23,
    "blue": 24
}

# Switch → LED mapping (hardware mode)
SWITCH_TO_LED = {
    "sw1": "super_red",
    "sw2": "red",
    "sw3": "yellow",
    "sw4": "green",
    "sw5": "blue"
}

OLLAMA_MODEL = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
You are a command parser for a Raspberry Pi LED control system.

Valid outputs ONLY:
- on <color>
- off <color>
- mode hardware
- mode manual
- mode ai

Valid colors:
super_red, red, yellow, green, blue

Return only one valid command.
Do not explain.
Do not add extra text.
"""

# ============================
# GPIO SETUP
# ============================

GPIO.setmode(GPIO.BCM)

for pin in SWITCH_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# ============================
# GLOBAL STATE
# ============================

mode = "hardware"
lock = threading.Lock()
last_switch_states = {}

# ============================
# HARDWARE MIRROR THREAD
# ============================

def hardware_loop():
    global last_switch_states
    while True:
        with lock:
            active_mode = mode

        if active_mode == "hardware":
            for sw, sw_pin in SWITCH_PINS.items():
                if sw in SWITCH_TO_LED:
                    led_name = SWITCH_TO_LED[sw]
                    led_pin = LED_PINS[led_name]

                    state = GPIO.input(sw_pin)

                    if state == GPIO.LOW:
                        GPIO.output(led_pin, GPIO.HIGH)
                    else:
                        GPIO.output(led_pin, GPIO.LOW)

        time.sleep(0.03)

# ============================
# AI COMMAND PARSER
# ============================

def parse_ai_command(user_text):
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return response["message"]["content"].strip()

# ============================
# TERMINAL COMMAND HANDLER
# ============================

def execute_command(cmd):
    global mode

    if cmd.startswith("mode"):
        parts = cmd.split()
        if len(parts) == 2 and parts[1] in ["hardware", "manual", "ai"]:
            with lock:
                mode = parts[1]
            print("Mode set to", mode)
        return

    parts = cmd.split()
    if len(parts) == 2:
        action, color = parts
        if color in LED_PINS:
            if action == "on":
                GPIO.output(LED_PINS[color], GPIO.HIGH)
            elif action == "off":
                GPIO.output(LED_PINS[color], GPIO.LOW)

# ============================
# INPUT LOOP
# ============================

def input_loop():
    global mode

    print("Final AI + Hardware GPIO Agent Active")
    print("Modes: hardware | manual | ai")
    print("Commands:")
    print("  mode hardware")
    print("  mode manual")
    print("  mode ai")
    print("  on <color> / off <color>")
    print("  exit")

    while True:
        try:
            user_input = input("> ").strip().lower()

            if user_input == "exit":
                break

            with lock:
                active_mode = mode

            if active_mode == "ai":
                parsed = parse_ai_command(user_input)
                print("AI →", parsed)
                execute_command(parsed)

            elif active_mode == "manual":
                execute_command(user_input)

            else:
                print("Hardware mode active; switches control LEDs")
        except KeyboardInterrupt:
            break

# ============================
# START THREADS
# ============================

hardware_thread = threading.Thread(target=hardware_loop, daemon=True)
hardware_thread.start()

try:
    input_loop()
finally:
    GPIO.cleanup()
    sys.exit(0)
