import flet as ft

from project.configuration.checkbox.reading_and_writing_checkbox_configuration import (
    reading_checkbox_configuration, writing_checkbox_configuration)


def create_settings_layer():
    """
    Создает интерфейс для настройки параметров станции с использованием чекбоксов.

    Возвращает:
    Tab: Объект вкладки с настройками.
    """
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

    settings_tab = ft.Tab(text="Настройки")
    outer_container = ft.Container(
        content=ft.Column(
            spacing=20,
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=20,
        expand=True,
        alignment=ft.alignment.center,
    )

    checkbox_labels = [
        "Выполнять подключение камер",
        # TODO: по сути это проверка камер, переделать надо
        "Выполнять калибровку станции",
        "Выполнять центровку корпусов",
        "Выполнять обнаружение объектов",
        "Выполнять универсальный алгоритм",
        "Выполнять фокусировку микроскопа",
        "Выполнять калибровку первой ячейки",
        # TODO: убрать, калибровка будет выполняться отдельно на второй вкладке
    ]

    checkboxes_per_row = 2
    config = reading_checkbox_configuration('checkbox.json')
    num_checkboxes = len(checkbox_labels)

    for i in range(0, num_checkboxes, checkboxes_per_row):
        row_controls = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=300,
                            content=ft.Text(
                                value=label, color=app_colors["text"], weight=ft.FontWeight.BOLD
                            ),
                            alignment=ft.alignment.center_left
                        ),
                        ft.Checkbox(
                            # Значение чекбокса из конфигурации
                            width=40,
                            height=40,
                            value=config.get(f"checkbox_{j + 1}", False),
                            on_change=lambda click, checkbox_id=f"checkbox_{j + 1}":
                                on_checkbox_change(click, checkbox_id)
                        )
                    ],
                    spacing=0,
                    alignment=ft.MainAxisAlignment.START
                ) for j, label in enumerate(checkbox_labels[i:i + checkboxes_per_row], start=i)
            ],
            spacing=150,
            alignment=ft.MainAxisAlignment.CENTER
        )
        outer_container.content.controls.append(row_controls)

    settings_tab.content = outer_container
    return settings_tab


def on_checkbox_change(e, checkbox_id):
    """
    Обрабатывает изменение состояния чекбокса и обновляет конфигурацию.

    Параметры:
    e: Событие изменения состояния.
    Checkbox_id (str): Идентификатор измененного чекбокса.

    Возвращает:
    NONE
    """
    # Чтение текущей конфигурации чекбоксов
    configuration = reading_checkbox_configuration('checkbox.json')

    # Обновление значения соответствующего чекбокса в конфигурации
    configuration[checkbox_id] = e.control.value

    # Запись обновленной конфигурации обратно в файл
    writing_checkbox_configuration(configuration, 'checkbox.json')
