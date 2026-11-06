import datetime
import flet as ft


def console_data_output(incoming_text_to_output_to_the_console, data_list, flag, text_color="white"):
    """
    Выводит текст в консоль и обновляет список консоли.

    Параметры:
    incoming_text_to_output_to_the_console (str): Текст для вывода в консоль.
    text_color (str): Цвет текста (например, "red", "green", "blue").

    Возвращает:
    None
    """
    optimized_text_for_console_output = f"[{
        datetime.datetime.now()}] {incoming_text_to_output_to_the_console}"
    print(optimized_text_for_console_output)

    if flag == "console":
        data_list[0].controls.append(
            ft.Text(optimized_text_for_console_output, size=16, color=text_color))
    elif flag == "errors":
        data_list[1].controls.append(
            ft.Text(optimized_text_for_console_output, size=16, color=text_color))
    else:
        data_list[0].controls.append(
            ft.Text(optimized_text_for_console_output, size=16, color=text_color))
        data_list[1].controls.append(
            ft.Text(optimized_text_for_console_output, size=16, color=text_color))

    for data in data_list:
        if data.page:
            data.update()
