import flet as ft

from project.application.modules.message import console_data_output

# Создание списка для отображения ошибок
errors_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
# Создание списка для отображения консольных сообщений
console_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)

# Объединение списков в один для дальнейшего использования
consoles_list = [console_list, errors_list]


def send_consoles_data(message, flag="console", color="#343e43"):
    """
    Отправляет сообщение в указанный консольный список.

    Параметры:
    message (str): Сообщение для отправки.
    flag (str): Указывает, в какой список отправить сообщение ("console" или "error").
    color (str): Цвет текста сообщения.

    Возвращает:
    NONE
    """
    console_data_output(
        message, consoles_list, flag, text_color=color)  # Вызов функции для вывода данных
    