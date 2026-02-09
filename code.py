import time
import board
import usb_hid
from adafruit_hid.mouse import Mouse
import digitalio

tickle_interval = 5 * 60  # 5min
jiggle_distance = 1


def main():
    mouse = Mouse(usb_hid.devices)

    led = digitalio.DigitalInOut(board.YELLOW_LED_INVERTED)
    led.direction = digitalio.Direction.OUTPUT

    log("Mouse jiggler started!")
    log("Interval", tickle_interval, "s")
    log("Distance ±", jiggle_distance, "px")
    log("Enter main loop...")

    while True:
        secs_to_go = tickle_interval
        while secs_to_go:
            log("Next jiggle in", secs_to_go, "s")
            secs_to_go -= 1
            blink(port=led)

        log("Jiggle jiggle!")
        jiggle(mouse, jiggle_distance)
        flash(port=led)


def flash(port):
    for _ in range(0, 10):
        blink(port=port, delay=.05)


def blink(port, delay=0.5):
    port.value = 1
    time.sleep(delay)
    port.value = 0
    time.sleep(delay)


def jiggle(mouse, distance=1):
    mouse.move(x=distance)
    mouse.move(x=-distance)


def log(*msg):
    print("MJ>", *msg)


main()