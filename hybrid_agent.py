import RPi.GPIO as GPIO
import time
import threading

SWITCH_PINS = {
    "sw1": 5,
    "sw2": 6,
    "sw3": 13,
    "sw4": 19,
    "sw5": 26,
    "sw6": 21
}

LED_PINS = {
    "super_red": 17,
    "red": 27,
    "yellow": 22,
    "green": 23,
    "blue": 24
}

SWITCH_TO_LED = {
    "sw1": "super_red",
    "sw2": "red",
    "sw3": "yellow",
    "sw4": "green",
    "sw5": "blue"
}

GPIO.setmode(GPIO.BCM)

for pin in SWITCH_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

mode = "hardware"
lock = threading.Lock()

def hardware_loop():
    global mode
    while True:
        with lock:
            local_mode = mode

        if local_mode == "hardware":
            for sw, sw_pin in SWITCH_PINS.items():
                if sw in SWITCH_TO_LED:
                    led_name = SWITCH_TO_LED[sw]
                    led_pin = LED_PINS[led_name]
                    state = GPIO.input(sw_pin)

                    if state == GPIO.LOW:
                        GPIO.output(led_pin, GPIO.HIGH)
                    else:
                        GPIO.output(led_pin, GPIO.LOW)
        time.sleep(0.05)

threading.Thread(target=hardware_loop, daemon=True).start()

print("Hybrid agent active.")
print("Modes: hardware | manual")
print("Commands: on red | off blue | mode hardware | mode manual | exit")

try:
    while True:
        cmd = input("> ").strip().lower()

        if cmd == "exit":
            break

        if cmd.startswith("mode"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ["hardware", "manual"]:
                with lock:
                    mode = parts[1]
                print("Mode set to", mode)
            continue

        with lock:
            if mode != "manual":
                print("Not in manual mode")
                continue

        parts = cmd.split()
        if len(parts) == 2:
            action, color = parts
            if color in LED_PINS:
                if action == "on":
                    GPIO.output(LED_PINS[color], GPIO.HIGH)
                elif action == "off":
                    GPIO.output(LED_PINS[color], GPIO.LOW)
        else:
            print("Invalid command")

finally:
    GPIO.cleanup()
