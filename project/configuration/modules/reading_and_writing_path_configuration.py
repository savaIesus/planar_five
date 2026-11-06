import os
import json

from project.application.modules.together import send_consoles_data


def reading_path_configuration(path_json_file_name):
    """
    Загружает пути из указанного файла конфигурации.

    Параметры:
    path_json_file_name (str): Путь к файлу конфигурации с путями.

    Возвращает:
    dict: Словарь с путями к весам нейросети для каждого квадрата.
    """
    path_json_file_name = f'project/configuration/modules/data/{path_json_file_name}'

    if not os.path.exists(path_json_file_name):
        send_consoles_data("Ошибка: конфигурационный файл paths.json не найден.", "errors", "red")
        return {}

    with open(path_json_file_name, 'r', encoding='utf-8') as file:
        data = file.read().strip()

        if not data:
            send_consoles_data("Ошибка: конфигурационный файл paths.json пустой.", "errors", "red")
            return {}

        try:
            config_dict = json.loads(data)
            return config_dict
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
            return {}


def writing_path_configuration(path_json_file_name, file_paths):
    """
    Обновляет пути в файле конфигурации только для переданных ключей, не изменяя остальные данные.

    Параметры:
    path_json_file_name (str): Путь к файлу конфигурации для сохранения путей.
    file_paths (dict): Словарь с путями к весам нейросети для каждого квадрата.

    Возвращает:
    None
    """
    path_json_file_name = f'project/configuration/modules/data/{path_json_file_name}'

    # Загружаем существующие данные, если файл существует
    if os.path.exists(path_json_file_name):
        with open(path_json_file_name, 'r', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Преобразуем абсолютные пути в относительные и обновляем только те ключи, которые переданы
    base_dir = os.getcwd()
    for key, value in file_paths.items():
        if value is not None:
            relative_path = os.path.relpath(value, base_dir)
            existing_data[key] = relative_path
        else:
            existing_data[key] = None

    # Записываем только обновленные данные в файл
    with open(path_json_file_name, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)
