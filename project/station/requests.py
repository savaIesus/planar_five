import time
import math
from flet import colors

from project.application.modules.together import send_consoles_data
from project.configuration.coordinates.reading_and_writing_coordinate_configuration import reading_coordinate_configuration
from project.configuration.coordinates.reading_and_writing_coordinate_configuration import writing_coordinate_configuration


def send_command(serial_connection, command):
    """
    Отправляет команду устройству через последовательное соединение.

    Параметры:
    serial_connection: Объект последовательного соединения.
    Command (str): Команда для отправки.

    Возвращает:
    str: Ответ от устройства или сообщение об ошибке.
    """
    serial_connection.write(f'{command}\n'.encode('utf-8'))

    # Чтение ответа
    response = serial_connection.readline()

    # Логирование необработанных байтов
    print(f"Raw response bytes: {response}")

    # Попытка декодирования с использованием различных кодировок
    for encoding in ['utf-8', 'ascii', 'iso-8859-1']:
        try:
            return response.decode(encoding).strip()

        except UnicodeDecodeError:
            continue

    return "Ошибка декодирования: данные не могут быть прочитаны."


def move_to_home(serial_connection):
    """
    Перемещает устройство в домашнее положение (0, 0, 0).

    Параметры:
    serial_connection: Объект последовательного соединения.
    """
    # Сброс координат
    zero_coordinates = [0, 0, 0]
    writing_coordinate_configuration('relevant_coordinates.json', *zero_coordinates)

    send_command(serial_connection, 'G28')
    start_time = time.time()
    timeout = 120

    while time.time() - start_time < timeout:
        send_consoles_data("Запрос состояния устройства.", "console")
        send_command(serial_connection, 'M27')

        response = serial_connection.readline().strip()
        send_consoles_data("Ответ устройства: выполняется калибровка.\n", "console", "yellow")
        print(response)
        if b'ok' in response:
            send_consoles_data("Ответ устройства: калибровка выполнена.\n", "console", "green")
            break
    else:
        send_consoles_data(
            "Ответ устройства: время калибровки истекло."
            "Проверьте концевики, питание и направление осей.\n", "console", "red"
        )
        raise TimeoutError("Калибровка не подтверждена контроллером")

    relevant_coordinates = reading_coordinate_configuration('relevant_coordinates.json')
    current_coordinates = [
        relevant_coordinates['x'], relevant_coordinates['y'], relevant_coordinates['z'] + 8]
    move_to_coordinates(serial_connection, *current_coordinates)


def move_to_coordinates(serial_connection, x=None, y=None, z=None):
    max_speed_z = 5
    max_speed_xy = 50

    prev_coordinates = reading_coordinate_configuration("relevant_coordinates.json")
    prev_x = prev_coordinates['x']
    prev_y = prev_coordinates['y']
    prev_z = prev_coordinates['z']

    def calculate_travel_time(x1, y1, z1, x2, y2, z2):
        distance_xy = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        distance_z = abs(z2 - z1)
        time_z = distance_z / max_speed_z
        time_xy = distance_xy / max_speed_xy
        return max(time_xy, time_z)

    command = 'G0'
    send_consoles_data("Запрос состояния устройства.", "console")

    if x is not None:
        command += f' X{x}'
    if y is not None:
        command += f' Y{y}'
    if z is not None:
        command += f' Z{z}'

    travel_time = calculate_travel_time(
        prev_x, prev_y, prev_z,
        x if x is not None else prev_x,
        y if y is not None else prev_y,
        z if z is not None else prev_z)

    send_command(serial_connection, command)
    send_consoles_data(
        f"Ответ устройства: установлены координаты: X={int(x)}, Y={int(y)}, Z={int(z)}\n",
        "console", colors.CYAN)

    start_time = time.time()

    while time.time() - start_time < travel_time:
        if not serial_connection.is_open:
            raise Exception("Соединение с устройством разорвано во время перемещения.")
        send_consoles_data("Запрос состояния устройства.", "console")
        send_consoles_data("Ответ устройства: выполняется перемещение.\n", "console", "yellow")
        time.sleep(1)

    send_consoles_data("Запрос состояния устройства.", "console")
    send_consoles_data("Ответ устройства: перемещение выполнено.\n", "console", "green")

    new_x = x if x is not None else prev_x
    new_y = y if y is not None else prev_y
    new_z = z if z is not None else prev_z

    writing_coordinate_configuration("relevant_coordinates.json", new_x, new_y, new_z)
