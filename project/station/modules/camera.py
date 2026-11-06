import cv2
import time
import base64
import threading

from project.application.modules.together import send_consoles_data

event = threading.Event()


def thread_init(index):
    if index == 1:
        event.set()
    elif index != 1:
        event.clear()


def camera_connection(camera_number):
    """
    Устанавливает соединение с камерой и устанавливает максимальное разрешение.

    Параметры:
    camera_number (int): Номер камеры для подключения.

    Возвращает:
    camera_data_stream (cv2.VideoCapture): Объект видеопотока камеры.

    Исключения:
    Выходит из программы, если камера не открыта.
    """
    camera_data_stream = cv2.VideoCapture(camera_number)

    if not camera_data_stream.isOpened():
        send_consoles_data("Ошибка: не удалось считать поток камеры.\n", "errors", "red")
        return False

    # Получаем максимальное доступное разрешение
    width = int(camera_data_stream.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera_data_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Устанавливаем максимальное разрешение
    camera_data_stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera_data_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    return camera_data_stream


def check_connected_cameras():
    """
    Проверяет, сколько камер доступно на системе.

    Возвращает:
    int: Количество доступных камер.
    """
    camera_count = 0

    while True:
        cap = cv2.VideoCapture(camera_count)

        if not cap.isOpened():
            break

        camera_count += 1
        cap.release()

    return camera_count


def check_camera_availability(camera_number):
    """
    Проверяет доступность камеры с заданным номером.

    Параметры:
    camera_number (int): Номер камеры для проверки.

    Возвращает:
    int: Номер камеры, если она доступна, иначе None.
    """
    cap = cv2.VideoCapture(camera_number)
    if cap.isOpened():
        cap.release()
        return camera_number
    return None


def connecting_all_cameras():
    """
    Устанавливает соединение со всеми доступными камерами.

    Возвращает:
    List[cv2.VideoCapture]: Список объектов видеопотока для всех подключенных камер,
    или пустой список, если ни одна камера не подключена.
    """
    max_cameras_to_check = 5  # Укажите максимальное количество камер для проверки
    threads = []
    available_cameras = []

    def check_and_collect(ids):
        result = check_camera_availability(ids)
        if result is not None:
            available_cameras.append(result)

    # Запуск потоков для проверки доступности камер
    for camera_number in range(max_cameras_to_check):
        thread = threading.Thread(target=check_and_collect, args=(camera_number,))
        thread.start()
        threads.append(thread)

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()

    # Устанавливаем соединение с доступными камерами
    camera_streams = []
    for camera_number in sorted(available_cameras):  # Сортируем для предсказуемости порядка
        camera_stream = camera_connection(camera_number)
        if camera_stream is not None:
            camera_streams.append(camera_stream)

    return camera_streams


# TODO: не работает: идея хорошая, реализация трудная
def square_camera_feed(camera, update_left_square):
    """
    Отображает видеопоток с указанной камеры в заданном квадрате.

    Параметры:
    camera (cv2.VideoCapture): Объект видеопотока камеры.
    update_square_callback (function): Функция для обновления содержимого квадрата.
    """
    while True:
        ret, frame = camera.read()

        if not ret:
            send_consoles_data("Ошибка: не удалось считать кадр с камеры.\n", "errors", "red")
            break

        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()

        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        update_left_square(image_base64)


# TODO: работает, но бесполезно: удалить или приспособить
def camera_to_base64_to_string(camera_number, image_container):
    """

    """
    connection = camera_connection(camera_number)

    while True:
        if not event.is_set():
            connection.release()
            event.wait()
            connection = camera_connection(camera_number)
            continue

        ret, frame = connection.read()

        if not ret:
            time.sleep(1)
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        image_container.src_base64 = img_base64

        try:
            image_container.update()
        except RuntimeError:
            event.clear()
            return


def capture_single_image(camera_number, max_retries=3, retry_delay=1):
    """
    Захватывает одно изображение с камеры в максимальном разрешении и сохраняет его в памяти.
    Если не удается захватить изображение с первого раза, пытается снова несколько раз.

    Аргументы:
    - camera_number: Номер камеры для захвата изображения.
    - max_retries: Максимальное количество попыток захвата изображения (по умолчанию 3).
    - retry_delay: Задержка между попытками (по умолчанию 1 секунда).

    Возвращает:
    numpy.ndarray: Захваченное изображение в формате NumPy массива.

    Исключение:
    RuntimeError: Если не удалось захватить изображение после нескольких попыток.
    """
    camera_data_stream = camera_connection(camera_number)

    if not camera_data_stream:
        raise RuntimeError(f"Не удалось подключиться к камере {camera_number}")

    retries = 0
    while retries < max_retries:
        ret, frame = camera_data_stream.read()

        if ret:
            camera_data_stream.release()
            return frame
        else:
            retries += 1
            print(f"Попытка {retries} не удалась. Повторная попытка через {retry_delay} секунд...")
            time.sleep(retry_delay)

    camera_data_stream.release()
    raise RuntimeError(f"Не удалось захватить изображение с камеры после {max_retries} попыток.")
