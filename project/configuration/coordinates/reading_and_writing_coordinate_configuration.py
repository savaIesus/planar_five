import json


def reading_coordinate_configuration(coordinates_json_file_name):
    """
    Загружает координаты из указанного файла конфигурации.

    Параметры:
    the_path_to_the_coordinate_configuration_file (str): Путь к файлу конфигурации с координатами.

    Возвращает:
    dict: Словарь с координатами x, y и z.
    """
    coordinates_json_file_name = f'project/configuration/coordinates/data/{
        coordinates_json_file_name}'

    with open(coordinates_json_file_name, 'r', encoding="utf-8") as file:
        data = file.read()  # Чтение содержимого файла
        return json.loads(data)  # Преобразование JSON-строки в словарь


def writing_coordinate_configuration(coordinates_json_file_name, x_coordinate, y_coordinate, z_coordinate):
    """
    Сохраняет заданные координаты в указанный файл конфигурации.

    Параметры:
    x_coordinate (float): Координата по оси X.
    y_coordinate (float): Координата по оси Y.
    z_coordinate (float): Координата по оси Z.
    the_path_to_the_coordinate_configuration_file (str):
        Путь к файлу конфигурации для сохранения координат.

    Возвращает:
    None
    """
    coordinates_json_file_name = f'project/configuration/coordinates/data/{
        coordinates_json_file_name}'

    # Создание словаря с округлёнными координатами
    coordinates = {
        'x': round(x_coordinate, 1), 'y': round(y_coordinate, 1), 'z': round(z_coordinate, 1)}

    with open(coordinates_json_file_name, 'w', encoding="utf-8") as file:
        json.dump(coordinates, file)  # Запись словаря в файл в формате JSON
