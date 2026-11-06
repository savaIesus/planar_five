import io
import base64
import flet as ft
import numpy as np
from PIL import Image as PILImage

from project.station.modules.algorithms import main_algorithm, set_button_references, stop_algorithm, toggle_pause


def create_workspace_layer():
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

    workspace_tab = ft.Tab(text="Проверка")

    def create_square_container():
        return ft.Container(
            width=560,
            height=560,
            bgcolor=app_colors["inactive"],
            border_radius=10,
            alignment=ft.alignment.center,
            content=ft.Stack(
                controls=[
                    ft.Image(
                        src="project/application/assets/load_light.gif",
                        width=560,
                        height=560
                    )
                ]
            )
        )

    left_square = create_square_container()
    right_square = create_square_container()

    def square_click(e):
        for square_click_row in squares:
            for square in square_click_row:
                square.border = None
                square.update()

        e.control.border = ft.border.all(3, ft.colors.WHITE)
        e.control.update()

    squares = []

    for square_row in range(10):
        squares_structure = [
            ft.Container(
                width=50,
                height=50,
                bgcolor=app_colors["inactive"],
                border_radius=8,
                alignment=ft.alignment.center,
                data={'row': square_row, 'col': col},
                on_click=square_click
            )
            for col in range(10)
        ]
        squares.append(squares_structure)

    squares_container = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            value="Изображение с камеры",
                            weight=ft.FontWeight.BOLD,
                            size=20, offset=(0.68, -0.25),
                            color=app_colors["text"]
                        ),
                        alignment=ft.alignment.center
                    ),
                    left_square
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.Column(
                controls=[
                    ft.Text(
                        value="Визуализация палеты",
                        weight=ft.FontWeight.BOLD,
                        size=20, offset=(0.85, -0.5),
                        color=app_colors["text"]
                    ),
                    *[
                        ft.Row(
                            controls=squares[button_row],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER
                        ) for button_row in range(10)
                    ],
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            value="Поиск объектов на изображении",
                            weight=ft.FontWeight.BOLD,
                            size=20, offset=(0.325, -0.25),
                            color=app_colors["text"]
                        ),
                        alignment=ft.alignment.center
                    ),
                    right_square
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=64
    )

    def update_square(square_container, image_array):
        if isinstance(image_array, np.ndarray):
            image_pil = PILImage.fromarray(image_array)
            byte_io = io.BytesIO()
            image_pil.save(byte_io, format='PNG')
            byte_io.seek(0)
            encoded_image = base64.b64encode(byte_io.read()).decode('utf-8')
            square_container.content = ft.Image(
                src_base64=encoded_image, fit=ft.ImageFit.COVER, width=560, height=560)
            square_container.update()
        else:
            square_container.content = ft.Stack(
                controls=[
                    ft.Image(
                        src="project/application/assets/load_light.gif",
                        width=560,
                        height=560
                    )
                ]
            )
            square_container.update()

    def update_left_square(image_array):
        update_square(left_square, image_array)

    def update_right_square(image_array):
        update_square(right_square, image_array)

    # Клавиша запуска
    start_button = ft.ElevatedButton(
        text="Запуск",
        width=120,
        height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            overlay_color=app_colors["hover"],
            bgcolor=app_colors["inactive"],
            color=app_colors["text"],
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            animation_duration=300
        )
    )

    # Клавиша паузы
    pause_button = ft.ElevatedButton(
        text="Пауза",
        width=120,
        height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            overlay_color=app_colors["hover"],
            bgcolor="#FFA500",
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            animation_duration=300
        ),
        disabled=True
    )

    # Клавиша остановки
    stop_button = ft.ElevatedButton(
        text="Стоп",
        width=120,
        height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            overlay_color=app_colors["hover"],
            bgcolor=app_colors["red"],
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            animation_duration=300
        ),
        disabled=True
    )

    # Функция-обработчик запуска
    def on_start_click(e):
        # Блокировка клавиши запуска после нажатия
        start_button.disabled = True
        start_button.update()

        # Активация клавиш паузы и остановки
        pause_button.disabled = False
        pause_button.update()
        stop_button.disabled = False
        stop_button.update()

        # Запуск алгоритма
        main_algorithm(start_button, update_left_square, update_right_square, squares)

    # Назначение функций-обработчиков паузы и остановки
    start_button.on_click = on_start_click
    pause_button.on_click = lambda e: toggle_pause()
    stop_button.on_click = lambda e: stop_algorithm()

    # Передача ссылок на кнопки в algorithms.py
    set_button_references(start_button, pause_button, stop_button)

    # Ряд с кнопками
    buttons_row = ft.Row(
        controls=[start_button, pause_button, stop_button],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    main_workspace_container = ft.Column(
        controls=[
            squares_container,
            buttons_row,
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER
    )

    color_legend_labels = [
        ("Стекло", ft.colors.BLUE_200),
        ("Пузыри", ft.colors.LIGHT_BLUE_900),
        ("Опущение", ft.colors.CYAN),
        ("Раковины", ft.colors.YELLOW_200),
        ("Брак сварки", ft.colors.AMBER),
        ("Гнутые/Битые", ft.colors.PINK),
        ("Незаполнение", ft.colors.ORANGE),
        ("Залив монтажки", ft.colors.DEEP_PURPLE),
        ("Неплоскостность", ft.colors.INDIGO),
        ("Разновысотность", ft.colors.BROWN),
        ("Залив контактов", ft.colors.DEEP_ORANGE),
        ("Механика ободка", ft.colors.PURPLE),
        ("Окалины/Трещины", ft.colors.GREEN_300),
        ("Утяжки/Нависание", ft.colors.GREEN_900),
        ("Непараллельность", ft.colors.RED)
    ]

    elements_per_row = 5

    color_rows = [
        ft.Row(
            controls=[
                ft.Container(
                    width=20,
                    height=20,
                    border_radius=5,
                    bgcolor=color,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text(value=label, color=app_colors["text"]),
                    width=200,
                    alignment=ft.alignment.center_left
                )
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
        ) for label, color in color_legend_labels
    ]

    color_squares_controls = ft.Column(
        controls=[
            ft.Row(
                controls=color_rows[i:i + elements_per_row],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER
            ) for i in range(0, len(color_rows), elements_per_row)
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    workspace_container = ft.Column(
        controls=[main_workspace_container, color_squares_controls],
        spacing=50,
        alignment=ft.MainAxisAlignment.CENTER
    )

    workspace_tab.content = workspace_container
    return workspace_tab
