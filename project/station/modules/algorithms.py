import math
import threading
import time

import numpy
import cv2
import flet as ft

from project.station.modules.network import uploading_a_neural_network_model, process_frame, process_frame_alt
from project.station.modules.math import largest_rectangle
from project.station.connection import establishing_connection
from project.application.modules.squares import change_square_color
from project.application.modules.together import send_consoles_data
from project.station.requests import move_to_home, move_to_coordinates
from project.configuration.protocols.protocols import protocol_initialisation, protocol_finalization, adding_to_protocol
from project.configuration.modules.reading_and_writing_path_configuration import reading_path_configuration
from project.configuration.checkbox.reading_and_writing_checkbox_configuration import reading_checkbox_configuration
from project.configuration.coordinates.reading_and_writing_coordinate_configuration import reading_coordinate_configuration


CONF = {
    "platform": 0.10,
    "contacts": 0.20,
    "glass_top": 0.6,
    "sinks": 0.40,
    "mechanics": 0.30,
    "bottom_glass": 0.80,
    "side_x": 0.10,
    "omission_x": 0.10,
    "flatness_x": 0.10,
    "side_y": 0.10,
    "omission_y": 0.10,
    "flatness_y": 0.10,
}


camera_threads = []

# Глобальные флаги работы/паузы/остановки
pause_flag = False
stop_flag = False
algorithm_running = False

# Глобальные ссылки на кнопки запуска/паузы/остановки
pause_button_ref = None
stop_button_ref = None
start_button_ref = None


def toggle_pause():
    """Переключение паузы"""
    global pause_flag
    pause_flag = not pause_flag
    status = "приостановлен" if pause_flag else "возобновлен"
    send_consoles_data(f"Алгоритм {status}", "console", "yellow" if pause_flag else "green")

    # Изменение текста на кнопке
    if pause_button_ref:
        pause_button_ref.text = "Возобновить" if pause_flag else "Пауза"
        pause_button_ref.icon = ft.icons.PLAY_ARROW if pause_flag else ft.icons.PAUSE
        pause_button_ref.update()

    return pause_flag


def stop_algorithm():
    """Остановка алгоритма"""
    global stop_flag, algorithm_running
    stop_flag = True
    algorithm_running = False
    send_consoles_data("Алгоритм остановлен", "console", "red")

    # Освобождение камер
    global camera_threads
    for camera_thread in camera_threads:
        camera_thread.stop()
        camera_thread.join()
    camera_threads.clear()

    # Возвращение кнопок в исходное состояние
    if start_button_ref:
        start_button_ref.disabled = False
        start_button_ref.update()
    if pause_button_ref:
        pause_button_ref.disabled = True
        pause_button_ref.text = "Пауза"
        pause_button_ref.icon = ft.icons.PAUSE
        pause_button_ref.update()
    if stop_button_ref:
        stop_button_ref.disabled = True
        stop_button_ref.update()


def check_pause_and_stop():
    """Проверка состояния паузы и остановки.
       Возвращает False, если нужно прервать выполнение."""
    global pause_flag, stop_flag

    # Сначала проверка на остановку (приоритет выше)
    if stop_flag:
        return False

    # Затем проверка на паузу
    while pause_flag and not stop_flag:
        time.sleep(0.1)
        # Если во время паузы нажата остановка - выход из алгоритма
        if stop_flag:
            return False

    return True


def set_button_references(start_btn, pause_btn, stop_btn):
    """Установка ссылок на кнопки для управления из алгоритма"""
    global start_button_ref, pause_button_ref, stop_button_ref
    start_button_ref = start_btn
    pause_button_ref = pause_btn
    stop_button_ref = stop_btn


class CameraThread(threading.Thread):
    """
    Класс для работы с потоками камер.
    """
    def __init__(self, camera_id):
        """
        Инициализация объекта CameraThread.

        Параметры:
        camera_id (int): Идентификатор камеры.
        """
        super().__init__()
        self.camera_id = camera_id
        self.capture = None
        self.running = False
        self._stop_event = threading.Event()
        self._frame_lock = threading.Lock()
        self._latest_frame = None
        self._error_logged = False
        self._consecutive_errors = 0
        self._started_event = threading.Event()

    def run(self):
        """
        Запуск потока для работы с камерой.
        """
        self.capture = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)

        if not self.capture.isOpened():
            print(f"[Camera {self.camera_id}] Не удалось открыть камеру")
            self._started_event.set()
            return

        try:
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            print(f"Ошибка захвата кадра с камеры: {e}")

        self.running = True
        self._started_event.set()

        while not self._stop_event.is_set():
            ret, frame = self.capture.read()

            if ret and frame is not None:
                with self._frame_lock:
                    self._latest_frame = frame
                self._consecutive_errors = 0
                self._error_logged = False
            else:
                self._consecutive_errors += 1

                if not self._error_logged:
                    print(f"[Camera {self.camera_id}] Ошибка захвата кадра. "
                          f"Переподключение через 1 с...")
                    self._error_logged = True

                # После 10 ошибок подряд выполняется переподключение к камере
                if self._consecutive_errors >= 10:
                    self._reconnect()

                # Задержка переподключения
                time.sleep(0.05)

        if self.capture is not None and self.capture.isOpened():
            self.capture.release()

    def _reconnect(self):
        """
        Переподключение к камере после серии ошибок.
        """
        try:
            if self.capture is not None:
                self.capture.release()
        except Exception as e:
            print(f"Ошибка освобождения камеры: {e}")

        time.sleep(0.5)

        try:
            self.capture = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            self.capture = None
            print(f"Ошибка переподключения к камере: {e}")

        self._consecutive_errors = 0

    def get_frame(self):
        """
        Получение текущего кадра с камеры.

        Возвращает:
        numpy.ndarray: Кадр с камеры или None, если не удалось получить.
        """
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def stop(self):
        """
        Остановка работы потока и освобождение ресурсов камеры.
        """
        self._stop_event.set()
        self.running = False

# Вспомогательные функции
def process_obodok(frame):
    """
    Обработка кадра: вырезает ободок из центра и помещает его на чёрный фон.

    Args:
        frame: numpy array (изображение в формате BGR)

    Returns:
        processed_frame: обработанный кадр с ободком на чёрном фоне
    """
    if frame is None:
        return frame

    h, w = frame.shape[:2]

    # ПАРАМЕТРЫ ОБРАБОТКИ
    crop1_width = 310  # размер ободка (внешний)
    crop1_height = 460

    crop2_width = 145  # размер внутренней дырки
    crop2_height = 260

    offset_x = 3  # Сдвигаем на 3 пикселя вправо
    offset_y = 0  # По вертикали не сдвигаем

    # ПРОВЕРКА РАЗМЕРОВ
    if crop1_width > w or crop1_height > h:
        print(f"⚠️ Кадр слишком мал ({w}x{h}) для crop1 ({crop1_width}x{crop1_height})")
        return frame

    if crop2_width > crop1_width or crop2_height > crop1_height:
        print(f"⚠️ crop2 ({crop2_width}x{crop2_height}) больше crop1 ({crop1_width}x{crop1_height})")
        return frame

    # Создаём чёрный фон
    result = frame.copy()
    result[:] = [0, 0, 0]

    # Вычисляем координаты со смещением
    x1 = (w - crop1_width) // 2 + offset_x
    y1 = (h - crop1_height) // 2 + offset_y

    # Ограничиваем координаты
    x1 = max(0, min(x1, w - crop1_width))
    y1 = max(0, min(y1, h - crop1_height))
    x2 = x1 + crop1_width
    y2 = y1 + crop1_height

    # Вырезаем ободок и делаем дырку
    obodok = frame[y1:y2, x1:x2].copy()

    ix1 = (crop1_width - crop2_width) // 2
    iy1 = (crop1_height - crop2_height) // 2
    ix2 = ix1 + crop2_width
    iy2 = iy1 + crop2_height

    obodok[iy1:iy2, ix1:ix2] = [0, 0, 0]

    # Вставляем ободок на чёрный фон
    result[y1:y2, x1:x2] = obodok

    return result

def disable_buttons(button, squares):
    """
    Отключение кнопок и обновление их состояния.

    Параметры:
    button (Button): Кнопка, которую нужно отключить.
    squares (list): Список квадратов, которые нужно отключить.
    """
    button.disabled = True
    button.update()

    for squares_row in squares:
        for square in squares_row:
            square.disabled = True
            square.update()


def enabling_buttons(button, squares):
    """
    Включение кнопок и обновление их состояния.

    Параметры:
    button (Button): Кнопка, которую нужно включить.
    squares (list): Список квадратов, которые нужно включить.
    """
    button.disabled = False
    button.update()

    for squares_row in squares:
        for square in squares_row:
            square.disabled = False
            square.update()


def moving_first_cell(serial_connection):
    """
    Перемещение на первую ячейку по заданным координатам.

    Параметры:
    serial_connection (Serial): Соединение с устройством.
    """
    cell_coordinates = reading_coordinate_configuration('cell_coordinates.json')
    current_coordinates = [
        cell_coordinates['x'],
        cell_coordinates['y'],
        cell_coordinates['z']
    ]
    move_to_coordinates(serial_connection, *current_coordinates)


# Основные функции
def main_algorithm_cameras(serial_connection, update_left_square, update_right_square, squares):
    """
    Алгоритм работы с пятью камерами.

    Параметры:
    serial_connection (Serial): Соединение с устройством.
    update_left_square (function): Функция для обновления левого квадрата.
    update_right_square (function): Функция для обновления правого квадрата.
    squares (list): Список квадратов для управления.
    """
    global camera_threads, pause_flag, stop_flag, algorithm_running

    camera_threads = []
    stop_flag = False
    pause_flag = False
    algorithm_running = True

    protocol = protocol_initialisation()

    try:
        move_to_home(serial_connection)
        moving_first_cell(serial_connection)

        camera_threads = [CameraThread(i) for i in range(5)]

        for camera_thread in camera_threads:
            camera_thread.daemon = True
            camera_thread.start()

        for camera_thread in camera_threads:
            while not camera_thread.capture or not camera_thread.capture.isOpened():
                time.sleep(0.1)

        current_coordinates = None

        config_file_name = "paths.json"
        paths = reading_path_configuration(config_file_name)

        # Блок центральной камеры
        model_case_side = uploading_a_neural_network_model(paths.get("Сторона корпуса"))
        if not model_case_side:
            send_consoles_data("Ошибка загрузки модели [Сторона корпуса].", "console", "red")
            return

        model_zaliv_montajki12n = uploading_a_neural_network_model(paths.get("Площадка"))
        if not model_zaliv_montajki12n:
            send_consoles_data("Ошибка загрузки модели [Площадка].", "console", "red")
            return

        model_zaliv_kontaktov_yolo26n = uploading_a_neural_network_model(paths.get("Контакты"))
        if not model_zaliv_kontaktov_yolo26n:
            send_consoles_data("Ошибка загрузки модели [Контакты].", "console", "red")
            return

        model_steklo12n = uploading_a_neural_network_model(paths.get("Стекло"))
        if not model_steklo12n:
            send_consoles_data("Ошибка загрузки модели [Стекло].", "console", "red")
            return

        model_bottom_glass = uploading_a_neural_network_model(paths.get("Стекло на дне"))
        if not model_bottom_glass:
            send_consoles_data("Ошибка загрузки модели [Стекло на дне].", "console", "red")
            return

        model_rakovini_puziri12n = uploading_a_neural_network_model(paths.get("Раковины"))
        if not model_rakovini_puziri12n:
            send_consoles_data("Ошибка загрузки модели [Раковины].", "console", "red")
            return

        model_top_mechanics = uploading_a_neural_network_model(paths.get("Механика ободка"))
        if not model_top_mechanics:
            send_consoles_data("Ошибка загрузки модели [Механика ободка].", "console", "red")
            return

        model_bottom_welding = uploading_a_neural_network_model(paths.get("Механика ободка"))
        if not model_bottom_welding:
            send_consoles_data("Ошибка загрузки модели [Механика ободка].", "console", "red")
            return

        # Блок левой и правой камеры
        model_top_or_bot_side_x = uploading_a_neural_network_model(paths.get("Сторона корпуса Х"))
        if not model_top_or_bot_side_x:
            send_consoles_data("Ошибка загрузки модели [Сторона корпуса Х].", "console", "red")
            return

        model_opushenie_korotkaya12n = uploading_a_neural_network_model(paths.get("Опущение X"))
        if not model_opushenie_korotkaya12n:
            send_consoles_data("Ошибка загрузки модели [Опущение X].", "console", "red")
            return

        model_flatness = uploading_a_neural_network_model(paths.get("Неплоскостность"))
        if not model_flatness:
            send_consoles_data("Ошибка загрузки модели [Неплоскостность].", "console", "red")
            return

        # Блок дальней и ближней камеры
        model_top_or_bot_side_y = uploading_a_neural_network_model(paths.get("Сторона корпуса Y"))
        if not model_top_or_bot_side_y:
            send_consoles_data("Ошибка загрузки модели [Сторона корпуса Y].", "console", "red")
            return

        model_side_omission_long = uploading_a_neural_network_model(paths.get("Опущение Y"))
        if not model_side_omission_long:
            send_consoles_data("Ошибка загрузки модели [Опущение Y].", "console", "red")
            return

        model_side_flatness_long = uploading_a_neural_network_model(paths.get("Неплоскостность"))
        if not model_side_flatness_long:
            send_consoles_data("Ошибка загрузки модели [Неплоскостность].", "console", "red")
            return

        for i in range(10):
            # Проверка паузы/остановки перед каждым рядом
            if not check_pause_and_stop():
                return
            for j in range(10):
                # Проверка паузы/остановки перед каждой ячейкой
                if not check_pause_and_stop():
                    return
                captured_frames = {}
                timeout = time.time() + 10

                while len(captured_frames) < len(camera_threads):
                    # Проверка паузы/остановки внутри цикла захвата
                    if not check_pause_and_stop():
                        return
                    for idx, camera_thread in enumerate(camera_threads):
                        if idx not in captured_frames:
                            frame = camera_thread.get_frame()
                            if frame is not None:
                                captured_frames[idx] = frame
                                update_left_square(frame)

                        if time.time() > timeout:
                            send_consoles_data(
                                "Ошибка: не удалось получить кадры со всех камер. "
                                "Выполняется переподключение.\n",
                                "console",
                                "red",
                            )

                            if camera_thread.capture and camera_thread.capture.isOpened():
                                camera_thread.capture.release()

                            camera_thread.capture = cv2.VideoCapture(camera_thread.camera_id, cv2.CAP_DSHOW)
                            timeout = time.time() + 10

                change_square_color(
                    squares,
                    9 - i,
                    j if i % 2 == 0 else 9 - j,
                    ft.colors.GREEN,
                )
                adding_to_protocol(i, j, "good", protocol)

                for idx, frame in captured_frames.items():
                    # Блок центральной камеры
                    if idx == 4:
                        # Блок обработки платформы
                        processed_frame, object_data = process_frame(
                            frame, model_zaliv_montajki12n, CONF["platform"])
                        coordinates = None

                        for item in object_data:
                            if item.get("class_name") == "objects":
                                coordinates = item["segment"]
                                break

                        if coordinates is not None:
                            points = numpy.array(coordinates, dtype=numpy.int32)
                            rectangle, _ = largest_rectangle(points)

                            if rectangle is not None:
                                cv2.polylines(
                                    processed_frame,
                                    [rectangle],
                                    True,
                                    (255, 0, 0),
                                    1,
                                )

                                _, _, w, h = cv2.boundingRect(rectangle)
                                print(w, h)

                                min_width = 85
                                max_width = 105
                                min_length = 175
                                max_length = 205

                                if not (
                                    min_width <= w <= max_width
                                    and min_length <= h <= max_length
                                ):
                                    change_square_color(
                                        squares,
                                        9 - i,
                                        j if i % 2 == 0 else 9 - j,
                                        ft.colors.DEEP_PURPLE,
                                    )
                                    adding_to_protocol(i, j, "platform", protocol)

                        # Блок обработки контактов
                        processed_frame, object_data = process_frame(
                            frame, model_zaliv_kontaktov_yolo26n, CONF["contacts"])

                        number_of_contacts = sum(
                            1 for item in object_data if item.get("class_name") == "contacts"
                        )

                        if number_of_contacts != 14:
                            change_square_color(
                                squares,
                                9 - i,
                                j if i % 2 == 0 else 9 - j,
                                ft.colors.DEEP_ORANGE,
                            )
                            adding_to_protocol(i, j, "contacts", protocol)
                        else:
                            for obj in object_data:
                                print(f"Площадь контакта: {obj.get('area', 0)}")

                                if obj.get("area", 0) < 600:
                                    change_square_color(
                                        squares,
                                        9 - i,
                                        j if i % 2 == 0 else 9 - j,
                                        ft.colors.DEEP_ORANGE,
                                    )
                                    adding_to_protocol(i, j, "contacts", protocol)

                        processed_frame, object_data = process_frame(
                            frame, model_steklo12n, CONF["glass_top"])

                        filtered_object_data = [
                            obj for obj in object_data
                            if 50 <= obj.get("area", 0) <= 600
                        ]

                        for obj in filtered_object_data:
                            print(
                                f"Объект стекла: {obj.get('class_name')}, "
                                f"Площадь: {obj.get('area', 0)}"
                            )

                        for item in filtered_object_data:
                            print(
                                f"Обрабатываем объект: {item.get('class_name')}, "
                                f"Площадь: {item.get('area', 0)}"
                            )

                            if item.get("class_name") == "steklo":
                                print(f"Обрабатываем стекло: {item.get('class_name')}")
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.BLUE_200,
                                )
                                adding_to_protocol(i, j, "glass", protocol)

                        # Блок обработки раковин
                        processed_frame, object_data = process_frame(
                            frame, model_rakovini_puziri12n, CONF["sinks"])

                        for item in object_data:
                            if item.get("class_name") == "Puzyri_Rakoviny":
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.YELLOW_200,
                                )
                                adding_to_protocol(i, j, "sinks", protocol)
                                break

                        # Блок обработки механики ободка
                        frame_for_mechanics = process_obodok(frame)
                        processed_frame, object_data = process_frame_alt(
                            frame_for_mechanics, model_top_mechanics, CONF["mechanics"])

                        for item in object_data:
                            if item.get("class_name") == "mechanica-obodka":
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.PURPLE,
                                )
                                adding_to_protocol(i, j, "mechanics", protocol)
                                break

                        update_right_square(processed_frame)

                        # Блок обработки стекла на дне
                        processed_frame, object_data = process_frame(
                            frame, model_bottom_glass, CONF["bottom_glass"])

                        for item in object_data:
                            if item.get("class_name") == "Glass on the assembly site":
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.BLUE_200,
                                )
                                adding_to_protocol(i, j, "glass", protocol)
                                break

                        update_right_square(processed_frame)

                    # Блок левой и правой камеры
                    if idx in (0, 3):
                        # Блок обработки опущения X
                        processed_frame, object_data = process_frame(
                            frame, model_opushenie_korotkaya12n, CONF["omission_x"])

                        for item in object_data:
                            if item.get("distance") > 25:
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.CYAN,
                                )
                                adding_to_protocol(i, j, "omission_short", protocol)
                                break

                        # Блок обработки разновысотности X
                        processed_frame, object_data = process_frame(
                            frame, model_flatness, CONF["flatness_x"])

                        flatness_objects = [
                            obj for obj in object_data
                            if obj["class_name"] == "flatness"
                        ][:2]

                        center_points = []

                        for obj in flatness_objects:
                            segment = numpy.array(obj["segment"])
                            M = cv2.moments(segment)

                            if M["m00"] != 0:
                                cX = int(M["m10"] / M["m00"])
                                cY = int(M["m01"] / M["m00"])
                                center_points.append((cX, cY))
                                cv2.circle(
                                    processed_frame,
                                    (cX, cY),
                                    3,
                                    [0, 0, 255],
                                    -1,
                                )

                        if len(center_points) == 2:
                            pt1, pt2 = center_points[0], center_points[1]

                            delta_y = pt2[1] - pt1[1]
                            delta_x = pt2[0] - pt1[0]
                            angle = math.degrees(math.atan2(delta_y, delta_x))

                            angle = angle % 360

                            if angle > 180:
                                angle = 360 - angle

                            angle_display = 180 - angle if angle > 90 else angle

                            cv2.line(processed_frame, pt1, pt2, [255, 0, 0], 2)

                            mid_point = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
                            cv2.putText(
                                processed_frame,
                                f"{angle_display:.1f}",
                                (mid_point[0], mid_point[1] - 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                [255, 0, 0],
                                2,
                            )

                            threshold_angle = 5

                            if angle_display > threshold_angle:
                                print(f"Обнаружен критический угол: {angle_display:.2f}°")
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.BROWN,
                                )
                                adding_to_protocol(i, j, "flatness", protocol)
                        else:
                            print(
                                f"Для анализа требуется 2 объекта, "
                                f"получено: {len(center_points)}"
                            )

                        update_right_square(processed_frame)

                    # Блок дальней и ближней камеры
                    if idx in (1, 2):
                        # Блок обработки опущения Y
                        processed_frame, object_data = process_frame(
                            frame, model_side_omission_long, CONF["omission_y"])

                        for item in object_data:
                            if item.get("distance") > 25:
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.CYAN,
                                )
                                adding_to_protocol(i, j, "omission", protocol)
                                break

                        # Блок обработки неплоскостности Y
                        processed_frame, object_data = process_frame(
                            frame, model_side_flatness_long, CONF["flatness_y"])

                        flatness_objects = [
                            obj for obj in object_data
                            if obj["class_name"] == "flatness"
                        ][:5]

                        center_points = []

                        for obj in flatness_objects:
                            segment = numpy.array(obj["segment"])
                            M = cv2.moments(segment)

                            if M["m00"] != 0:
                                cX = int(M["m10"] / M["m00"])
                                cY = int(M["m01"] / M["m00"])
                                center_points.append((cX, cY))

                                cv2.circle(
                                    processed_frame,
                                    (cX, cY),
                                    3,
                                    [0, 0, 255],
                                    -1,
                                )

                        if len(center_points) == 2:
                            pt1, pt2 = center_points[0], center_points[1]

                            delta_y = pt2[1] - pt1[1]
                            delta_x = pt2[0] - pt1[0]
                            angle = math.degrees(math.atan2(delta_y, delta_x))

                            angle = angle % 360

                            if angle > 180:
                                angle = 360 - angle

                            angle_display = 180 - angle if angle > 90 else angle

                            cv2.line(processed_frame, pt1, pt2, [255, 0, 0], 2)

                            mid_point = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
                            cv2.putText(
                                processed_frame,
                                f"{angle_display:.1f}",
                                (mid_point[0], mid_point[1] - 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                [255, 0, 0],
                                2,
                            )

                            threshold_angle = 5

                            if angle_display > threshold_angle:
                                print(f"Обнаружен критический угол: {angle_display:.2f}°")
                                change_square_color(
                                    squares,
                                    9 - i,
                                    j if i % 2 == 0 else 9 - j,
                                    ft.colors.BROWN,
                                )
                                adding_to_protocol(i, j, "flatness", protocol)
                        else:
                            print(f"Для анализа требуется 2 объекта, получено: {len(center_points)}")

                        update_right_square(processed_frame)

                time.sleep(0.1)

                relevant_coordinates = reading_coordinate_configuration("relevant_coordinates.json")
                current_coordinates = [
                    relevant_coordinates["x"],
                    relevant_coordinates["y"],
                    relevant_coordinates["z"],
                ]

                if j != 9:
                    current_coordinates[0] += 18.7 if i % 2 == 0 else -18.7
                    move_to_coordinates(serial_connection, *current_coordinates)

            current_coordinates[1] += 19.2
            move_to_coordinates(serial_connection, *current_coordinates)

    finally:
        protocol_finalization(protocol)
        close(0)

def close(_e):
    for camera_thread in camera_threads:
        camera_thread.stop()
        camera_thread.join()

def main_algorithm(button, update_left_square, update_right_square, squares):
    """
    Общий алгоритм работы программы.

    Параметры:
    button (Button): Кнопка управления.
    update_left_square (function): Функция для обновления левого квадрата.
    update_right_square (function): Функция для обновления правого квадрата.
    squares (list): Список квадратов для управления.
    """
    global stop_flag, algorithm_running

    # Сброс флагов работы/паузы/остановки перед запуском
    stop_flag = False
    algorithm_running = False
    disable_buttons(button, squares)

    for row in range(10):
        for col in range(10):
            change_square_color(squares, row, col, "grey")

    configuration = reading_checkbox_configuration("checkbox.json")
    if configuration.get('checkbox_2'):
        with establishing_connection(button, squares) as serial_connection:
            move_to_home(serial_connection)

    if configuration.get('checkbox_7'):
        moving_first_cell(serial_connection)

    if configuration.get('checkbox_5'):
        send_consoles_data("Запрос выполнения алгоритма.", "console")

        if configuration.get('checkbox_1'):
            send_consoles_data(
                "Ответ устройства: алгоритм успешно инициализирован.\n",
                "console", "green")

            with establishing_connection(button, squares) as serial_connection:
                algorithm_running = True
                if configuration.get("checkbox_7"):
                    moving_first_cell(serial_connection)
                main_algorithm_cameras(
                    serial_connection,
                    update_left_square,
                    update_right_square,
                    squares,
                )
                algorithm_running = False
        else:
            send_consoles_data(
                "Ошибка: подключение камер отключено в настройках.",
                "console", "red")

    enabling_buttons(button, squares)
    return
