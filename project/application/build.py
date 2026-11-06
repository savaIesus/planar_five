import flet as ft

from project.application.tab_control import tab_control
from project.application.list import create_layers_list
from project.station.modules.algorithms import close


def building_the_application(application_page: ft.Page):
    """
    Строит интерфейс приложения, настраивая размеры окна и добавляя вкладки.

    Параметры:
    application_page (Page): Объект страницы приложения, в которую будут добавлены вкладки.

    Возвращает:
    None
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

    # Установка размеров окна приложения
    application_page.window_width = 1920
    application_page.window_height = 1080
    application_page.window_title = "Название"

    application_page.title = "Управление системой"
    application_page.vertical_alignment = ft.MainAxisAlignment.CENTER
    application_page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Настройка цветовой гаммы приложения
    application_page.bgcolor = app_colors["background"]

    # Переключение в полноэкранный режим
    application_page.window_full_screen = False
    application_page.on_app_lifecycle_state_change = close

    # Создание вкладок приложения с заданными параметрами
    application_layers = ft.Tabs(
        expand=1,
        selected_index=0,
        on_change=tab_control,
        animation_duration=400,
        label_color=app_colors["active"],
        divider_color=app_colors["top_bar"],
        indicator_color=app_colors["active"],
        unselected_label_color=app_colors["text"],
        indicator_tab_size=True,
        tabs=create_layers_list()
    )

    # Добавление вкладок на страницу приложения
    application_page.add(application_layers)
