from project.application.layers.camera import create_camera_layer
from project.application.layers.errors import create_errors_layer
from project.application.layers.console import create_console_layer
from project.application.layers.settings import create_settings_layer
from project.application.layers.stats import create_statistics_layer
from project.application.layers.workspace import create_workspace_layer


def create_layers_list():
    """
    Создаёт и возвращает список слоёв приложения.

    Параметры:
    NONE

    Возвращает:
    list: Список объектов слоёв.
    """
    layers_list = [
        create_workspace_layer(),   # Создание слоя проверка
        create_camera_layer(),      # Создание слоя камеры
        create_settings_layer(),    # Создание слоя настроек
        create_console_layer(),     # Создание слоя консоли
        create_errors_layer(),      # Создание слоя ошибок
        create_statistics_layer()   # Создание слоя статистики
    ]

    return layers_list
