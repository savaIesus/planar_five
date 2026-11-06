import os
import time
import base64
import keyboard
import threading
import flet as ft
from io import BytesIO
from PIL import Image as PILImage

from project.station.connection import establishing_connection
from project.station.requests import move_to_coordinates
from project.station.modules.camera import camera_to_base64_to_string
from project.configuration.coordinates.reading_and_writing_coordinate_configuration import (
    reading_coordinate_configuration, writing_coordinate_configuration)

calibration = threading.Event()
calibration.clear()


def calibration_thread_init(index):
    if index == 1:
        calibration.set()
    elif index != 1:
        calibration.clear()


def moving(serial_connection, axis):
    current_coordinates = None
    cell_coordinates = reading_coordinate_configuration('cell_coordinates.json')

    value = 1

    if axis == "-x":
        current_coordinates = [
            cell_coordinates['x'] - value, cell_coordinates['y'], cell_coordinates['z']]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)
    if axis == "+x":
        current_coordinates = [
            cell_coordinates['x'] + value, cell_coordinates['y'], cell_coordinates['z']]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)
    if axis == "-y":
        current_coordinates = [
            cell_coordinates['x'], cell_coordinates['y'] - value, cell_coordinates['z']]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)
    if axis == "+y":
        current_coordinates = [
            cell_coordinates['x'], cell_coordinates['y'] + value, cell_coordinates['z']]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)
    if axis == "-z":
        current_coordinates = [
            cell_coordinates['x'], cell_coordinates['y'], cell_coordinates['z'] - value]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)
    if axis == "+z":
        current_coordinates = [
            cell_coordinates['x'], cell_coordinates['y'], cell_coordinates['z'] + value]
        writing_coordinate_configuration(
            "cell_coordinates.json", *current_coordinates)

    move_to_coordinates(serial_connection, *current_coordinates)


# Функция для работы с камерами
def cameras_threads(camera_number, image_container):
    while True:
        try:
            image_data = camera_to_base64_to_string(camera_number, image_container)
            if image_data is not None:
                image_container.src_base64 = image_data
                image_container.src = None
                image_container.update()
            else:
                image_container.src_base64 = None
                image_container.src = "project/application/assets/load_light.gif"
                image_container.update()
                print(f"Camera {camera_number} returned no data.")
        except Exception as e:
            print(f"Error accessing camera {camera_number}: {e}")


# TODO: шляпа не работающая, описание ниже в пунктике 0 (кликаем на клавикатуру)
# Функция для сохранения изображения
def save_image_from_base64(image_data, camera_index):
    try:
        # Преобразуем base64 строку в изображение
        image_data_bytes = base64.b64decode(image_data)
        image = PILImage.open(BytesIO(image_data_bytes))

        # Путь к папке для сохранения
        save_path = f"dataset/{camera_index + 1}"  # Папка для каждой камеры (1, 2, 3, 4, 5)

        # Создаём папку, если она не существует
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # Путь для сохранения изображения
        image.save(f"{save_path}/frame_{int(time.time())}.png")
        print(f"Кадр с камеры {camera_index} сохранён в {save_path}.")
    except Exception as e:
        print(f"Ошибка при сохранении изображения с камеры {camera_index}: {e}")


def keyboard_listener(image_containers):
    serial_connection = establishing_connection()
    if serial_connection is None:
        return None

    while True:
        if not calibration.is_set():
            serial_connection.close()
            calibration.wait()
            serial_connection = establishing_connection()
            continue

        if keyboard.is_pressed('8'):  # Нажатие на 8
            moving(serial_connection, "+y")
        elif keyboard.is_pressed('2'):  # Нажатие на 2
            moving(serial_connection, "-y")
        elif keyboard.is_pressed('4'):  # Нажатие на 4
            moving(serial_connection, "-x")
        elif keyboard.is_pressed('6'):  # Нажатие на 6
            moving(serial_connection, "+x")
        elif keyboard.is_pressed('7'):  # Нажатие на 7
            print("Нажата клавиша 7 на нампаде: выполняем действие 5")
        elif keyboard.is_pressed('9'):  # Нажатие на 9
            moving(serial_connection, "+z")
        elif keyboard.is_pressed('1'):  # Нажатие на 1
            moving(serial_connection, "-z")
        elif keyboard.is_pressed('3'):  # Нажатие на 3
            print("Нажата клавиша 3 на нампаде: выполняем действие 8")
        elif keyboard.is_pressed('5'):  # Нажатие на 5
            print("Нажата клавиша 5 на нампаде: выполняем действие 9")
        # TODO: не работает ибо камеры и так крутятся, а мы просто хотим ещё раз с них вытащить кадр, подумать надо
        elif keyboard.is_pressed('0'):  # Нажатие на 0
            print("Нажата клавиша 0 на нампаде: сохраняем кадры с камер")
            # Сохраняем кадры с каждой камеры
            for i in range(5):
                image_data = camera_to_base64_to_string(i, image_containers[i])
                if image_data:
                    save_image_from_base64(image_data, i)
        time.sleep(0.01)

def create_camera_layer():
    app_colors = {
        "red": "#ea1a1a",                 # Красный цвет для слайдера красного фильтра
        "light_red": "#f04242",           # Бледно-красный цвет для измерительных фигур
        "text": "#343e43",                # Текст
        "hover": "#40a8ee",               # Кнопки, на которые наведён курсор
        "green": "#2bda6a",               # Зелёный цвет для слайдера зелёного фильтра
        "active": "#1592e6",              # Заполненные области и рукояти слайдеров, нажатые кнопки
        "top_bar": "#e0e0e0",             # Верхняя полоса и контейнер для видео
        "inactive": "#cecece",            # Ненажатые кнопки, незаполненные области слайдеров
        "unclickable": "#9d9d9d",         # Недоступные сейчас кнопки
        "active_unclickable": "#3584b9",  # Выбранные, но недоступные сейчас кнопки
        "background": "#f5f5f5",          # Фон
    }

    image_containers = [
        ft.Image(
            width=320, height=320, src_base64="",
            src="project/application/assets/load_light.gif",
            fit=ft.ImageFit.COVER
        ) for _ in range(5)
    ]

    camera_layer = ft.Tab(text="Камеры")
    top_square = ft.Container(
        width=300,
        height=300,
        border_radius=16,
        bgcolor=app_colors["inactive"],
        alignment=ft.alignment.center,
        content=image_containers[2]
    )

    middle_row = ft.Row(
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=320, height=320, bgcolor=app_colors["inactive"], border_radius=20,
                alignment=ft.alignment.center, content=image_containers[0]),
            ft.Container(
                width=320, height=320, bgcolor=app_colors["inactive"], border_radius=20,
                alignment=ft.alignment.center, content=image_containers[4]),
            ft.Container(
                width=320, height=320, bgcolor=app_colors["inactive"], border_radius=20,
                alignment=ft.alignment.center, content=image_containers[3])
        ]
    )

    bottom_square = ft.Container(
        width=300,
        height=300,
        border_radius=16,
        bgcolor=app_colors["inactive"],
        alignment=ft.alignment.center,
        content=image_containers[1]
    )

    squares_container = ft.Column(
        spacing=10,
        controls=[top_square, middle_row, bottom_square],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    camera_layer.content = squares_container

    # Потоки для камер
    for i in range(5):
        camera_thread = threading.Thread(
            target=cameras_threads,
            args=(i, image_containers[i]),
            daemon=True
        )
        camera_thread.start()

    # Поток для отслеживания нажатий клавиш на нампаде
    keyboard_thread = threading.Thread(
        target=keyboard_listener,
        args=(image_containers,),  # Передаем image_containers в поток
        daemon=True
    )

    keyboard_thread.start()
    return camera_layer
