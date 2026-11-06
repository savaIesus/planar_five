import flet as ft

from project.application.modules.together import errors_list


def create_errors_layer():
    """
    Делает сборку слоя ошибок.

    Возвращает:
    Tab: Объект Tab, представляющий слой консоли.
    """
    errors_layer = ft.Tab(
        text="Ошибки",
        content=ft.Container(
            padding=20,
            expand=True,
            content=errors_list,
            alignment=ft.alignment.center
        )
    )
    return errors_layer
