import time
import usb_hid
import supervisor

from adafruit_hid.mouse import Mouse

tickle_interval = 5 * 60  # 5min
jiggle_distance = 1


def main():
    supervisor.set_usb_identification("CPY", "Mouse MJ2040")
    usb_hid.set_interface_name("CPY Mouse MJ2040")
    mouse = Mouse(usb_hid.devices)

    print("Mouse jiggler started!\n")
    print("Interval %s" % min_sec_fmt(tickle_interval))
    print("Distance ±%dpx" % jiggle_distance)
    print("Enter main loop...\n")

    while True:
        secs_to_go = tickle_interval
        print(" "*50, end="\r")

        while secs_to_go:
            print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="\r")
            secs_to_go -= 1
            time.sleep(1)

        print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="")
        print("Jiggle jiggle!", end="\r")
        jiggle(mouse, jiggle_distance)
        time.sleep(1)


def min_sec_fmt(duration):
    mins = duration/60
    secs = duration%60
    return "%dmin %dsec" % (mins, secs)


def jiggle(mouse, distance=1):
    mouse.move(x=distance)
    mouse.move(x=-distance)


main()