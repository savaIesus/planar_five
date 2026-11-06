import json


def reading_checkbox_configuration(checkbox_json_file_name):
    """
    Загружает конфигурацию чекбоксов из указанного файла.

    Параметры:
    the_path_to_the_coordinate_configuration_file (str): Путь к файлу конфигурации чекбоксов.

    Возвращает:
    dict: Словарь с конфигурацией чекбоксов.
    """
    checkbox_configuration_path = f'project/configuration/checkbox/{checkbox_json_file_name}'

    with open(checkbox_configuration_path, "r", encoding="utf-8") as file:
        data = file.read().strip()
        return json.loads(data)


def writing_checkbox_configuration(checkboxes_configuration, checkbox_json_file_name):
    """
    Сохраняет конфигурацию чекбоксов в указанный файл.

    Параметры:
    configuration_of_checkboxes (dict): Словарь с конфигурацией чекбоксов.
    the_path_to_the_coordinate_configuration_file (str):
        Путь к файлу для сохранения конфигурации чекбоксов.

    Возвращает:
    None
    """
    checkbox_configuration_path = f'project/configuration/checkbox/{checkbox_json_file_name}'

    with open(checkbox_configuration_path, "w", encoding="utf-8") as file:
        json.dump(checkboxes_configuration, file, indent=4)
