import flet as ft

from project.application.modules.together import console_list


def create_console_layer():
    """
    Делает сборку слоя консоли.

    Возвращает:
    Tab: Объект Tab, представляющий слой консоли.
    """
    console_layer = ft.Tab(
        text="Консоль",
        content=ft.Container(
            padding=20,
            expand=True,
            content=console_list,
            alignment=ft.alignment.center
        )
    )
    return console_layer
