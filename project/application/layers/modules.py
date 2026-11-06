import os
import json
import flet as ft

from project.application.modules.together import send_consoles_data
from project.configuration.modules.reading_and_writing_path_configuration import reading_path_configuration
from project.configuration.modules.reading_and_writing_path_configuration import writing_path_configuration

elements = [
    "Сторона корпуса", "Площадка", "Контакты", "Опущение X",
    "Опущение Y", "Сторона корпуса Y", "Сторона корпуса Х", "Стекло",
    "Раковины", "Неплоскостность", "Разновысотность", "Механика ободка",
    "Стекло на дне", "Сварка", "NONE", "NONE",
    "NONE", "NONE", "NONE", "NONE",
    "NONE", "NONE", "NONE", "NONE"
]

file_path = "project/configuration/modules/data/paths.json"

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        cnn_paths = json.load(file)
except FileNotFoundError:
    send_consoles_data("Файл с путями для нейросетей не найден", "error")

    cnn_paths = {element: None for element in elements}
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(cnn_paths, file, ensure_ascii=False, indent=4)


current_square_name = None


def on_file_selected(event):
    """
    Обработчик выбора файла, сохраняющий путь в словарь cnn_paths.
    """
    global cnn_paths, current_square_name
    if event.files and current_square_name:
        # Сохраняем путь выбранного файла
        cnn_paths[current_square_name] = event.files[0].path
        writing_path_configuration("paths.json", cnn_paths)


def select_file(square_name, file_picker_dial):
    """
    Запускает диалог выбора файла для указанного квадрата.
    """
    global current_square_name
    # Устанавливаем текущее название квадрата
    current_square_name = square_name

    # Открываем диалог выбора файла
    file_picker_dial.pick_files(
        dialog_title="Выберите файл весов нейросети",
        initial_directory=os.path.abspath("project\\station\\weights"),
        allowed_extensions=["pt"],
    )


def create_module_layer():
    console_layer = ft.Tab(text="Модули")
    square_names = [
        "Сторона корпуса", "Площадка", "Контакты", "Опущение X",
        "Опущение Y", "Сторона корпуса Y", "Сторона корпуса Х", "Стекло",
        "Раковины", "Неплоскостность", "Разновысотность", "Механика ободка",
        "Стекло на дне", "Сварка", "NONE", "NONE",
        "NONE", "NONE", "NONE", "NONE",
        "NONE", "NONE", "NONE", "NONE"
    ]

    reading_path_configuration("paths.json")
    for name in square_names:
        if name not in cnn_paths:
            cnn_paths[name] = None

    file_picker_dialog = ft.FilePicker()
    file_picker_dialog.on_result = on_file_selected

    squares_container = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Container(
                                width=125,
                                height=125,
                                bgcolor=ft.colors.RED,
                                alignment=ft.alignment.center,
                                content=None
                            ),
                            ft.Text(square_names[squares_row * 6 + col], size=14),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        text="+",
                                        width=60,
                                        on_click=lambda e, sn=square_names[
                                            squares_row * 6 + col]: select_file(sn, file_picker_dialog)
                                    ),
                                    ft.Switch(value=False)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ) for col in range(6)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=160
            ) for squares_row in range(4)
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER
    )

    console_layer.content = ft.Column(
        controls=[squares_container, file_picker_dialog],
        alignment=ft.MainAxisAlignment.CENTER
    )
    return console_layer
