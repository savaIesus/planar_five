import flet as ft


def create_about_layer():
    """
    Делает сборку слоя информации.

    Возвращает:
    Tab: Объект Tab, представляющий слой информации.
    """
    about_layer = ft.Tab(text="Информация")
    return about_layer
