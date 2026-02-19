import serial

from src.config import serial_drive_enable_command


def main():
    with serial.Serial("COM15", 115200) as com:
        com.write(f"{serial_drive_enable_command}\n".encode())


if __name__ == "__main__":
    main()
