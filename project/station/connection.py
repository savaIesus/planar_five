import serial
import serial.tools.list_ports

from project.application.modules.together import send_consoles_data


def port_detection():
    """
    Обнаруживает доступные последовательные порты и выбирает USB-серийный порт.

    Возвращает:
    str: Устройство USB-серийного порта или None, если не найдено.
    """
    ports = serial.tools.list_ports.comports()
    usb_serial_ports = [port for port in ports if "USB-SERIAL" in port.description.upper()]

    if usb_serial_ports:
        return usb_serial_ports[0].device

    return None


def defining_presets():
    """
    Определяет параметры соединения с устройством.

    Возвращает:
    tuple: Порт, скорость передачи данных и таймаут.
    """
    port = port_detection()
    baudrate = 115200
    timeout = 1

    return port, baudrate, timeout


def establishing_connection(button=None, squares=None):
    """
    Устанавливает соединение с устройством по обнаруженному порту.

    Возвращает:
    Serial: Объект соединения или None, если соединение не удалось установить.
    """
    port, baudrate, timeout = defining_presets()  # Получение параметров соединения
    send_consoles_data("Запрос соединения с устройством.", "console")

    try:
        connection = serial.Serial(port, baudrate, timeout=timeout)  # Установка соединения

        if connection.is_open:
            send_consoles_data(
                "Ответ устройства: соединение установлено.\n", "console", "green")
            return connection  # Возвращает объект соединения, если оно успешно открыто

        send_consoles_data(
            "Ошибка: провод не подключён физически или не установлен драйвер.\n", "both", "red")
        button.disabled = False
        button.update()

        for squares_row in squares:
            for square in squares_row:
                square.disabled = False
                square.update()

        return None

    except serial.serialutil.SerialException:
        send_consoles_data("Ошибка: отказано в доступе.\n", "both", "red")
        button.disabled = False
        button.update()

        for squares_row in squares:
            for square in squares_row:
                square.disabled = False
                square.update()
                return None

            return None

        return None
