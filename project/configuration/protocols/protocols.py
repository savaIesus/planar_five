import os
import json
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from project.configuration.protocols.publisher import push_file_to_pc2, sync_unsent_json_files
from project.application.modules.together import send_consoles_data


# Локальные папки на ПК инспекции
LOCAL_PROTOCOLS_ROOT = r"C:/Users/user/Desktop/Protocols"
LOCAL_JSON_DIR = os.path.join(LOCAL_PROTOCOLS_ROOT, "json")
LOCAL_EXCEL_DIR = os.path.join(LOCAL_PROTOCOLS_ROOT, "excel")


def protocol_initialisation():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    protocol_path = "project/configuration/protocols/data/protocols.json"

    try:
        os.makedirs(os.path.dirname(protocol_path), exist_ok=True)
        data = {"Start time": str(formatted_time)}

        with open(protocol_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False)

    except OSError:
        send_consoles_data("Ошибка: не удалось инициализировать протокол", "errors", "red")

    return protocol_path


def adding_to_protocol(vert, hor, defect_type, protocol_path):
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    try:
        with open(protocol_path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

        if "defects" not in existing_data:
            existing_data["defects"] = []

        found = False
        for item in existing_data["defects"]:
            if item["vert"] == vert and item["hor"] == hor:
                item["type"] = defect_type
                item["time"] = formatted_time
                found = True
                break

        if not found:
            existing_data["defects"].append(
                {"vert": vert, "hor": hor, "type": defect_type, "time": formatted_time}
            )

        with open(protocol_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

    except OSError:
        send_consoles_data("Ошибка: не удалось внести брак в протокол", "errors", "red")
    except json.JSONDecodeError:
        send_consoles_data("Ошибка: не удалось декодировать JSON", "errors", "red")
    except Exception as e:
        send_consoles_data(f"Ошибка в adding_to_protocol: {e}", "errors", "red")


def protocol_finalization(protocol_path):
    send_consoles_data("protocol_finalization() CALLED", "info", "green")
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    try:
        with open(protocol_path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

        existing_data["Finish time"] = str(formatted_time)

        # Сохраняем финальную версию data/protocols.json
        with open(protocol_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

        # 1) Сохраняем JSON в проект (на всякий)
        new_fname = f"Протокол_{formatted_time}.json"
        new_path_in_project = os.path.join("project/configuration/protocols", new_fname)

        with open(new_path_in_project, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

        # 2) Сохраняем JSON локально на рабочий стол ПК инспекции
        os.makedirs(LOCAL_JSON_DIR, exist_ok=True)
        local_json_path = os.path.join(LOCAL_JSON_DIR, new_fname)

        with open(local_json_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

        send_consoles_data(f"JSON сохранен локально: {local_json_path}", "info", "green")

        # 3) Сначала догружаем старые JSON, которые раньше не отправились
        try:
            synced_files = sync_unsent_json_files()

            if synced_files:
                send_consoles_data(
                    f"Догружено старых JSON на ПК аналитики: {len(synced_files)}",
                    "info", "green"
                )
            else:
                send_consoles_data(
                    "Старых JSON для догрузки нет или ПК аналитики недоступен",
                    "info", "orange"
                )

        except Exception as e:
            send_consoles_data(
                f"Не удалось выполнить догрузку старых JSON: {e}",
                "errors", "red"
            )

            # 4) Отправляем текущий JSON на ПК аналитики
            try:
                remote_json = push_file_to_pc2(local_json_path)

                if remote_json:
                    send_consoles_data(
                        f"Текущий JSON отправлен на ПК аналитики: {remote_json[0]}",
                        "info", "green"
                    )
                else:
                    send_consoles_data(
                        "Текущий JSON сохранён локально, но пока не отправлен на ПК аналитики",
                        "errors", "orange"
                    )

            except Exception as e:
                send_consoles_data(
                    f"Не удалось отправить текущий JSON на ПК аналитики: {e}",
                    "errors", "red"
                )

        # 5) Excel сохраняем локально
        saving_excel_protocol(existing_data)

    except OSError:
        send_consoles_data("Ошибка: не удалось завершить протокол", "errors", "red")
    except json.JSONDecodeError:
        send_consoles_data("Ошибка: не удалось декодировать JSON", "errors", "red")
    except Exception as e:
        send_consoles_data(f"Ошибка в protocol_finalization: {e}", "errors", "red")


def saving_excel_protocol(data: dict):
    """
    Делает Excel-отчет из уже загруженного JSON-словаря data, сохраняет локально.
    На ПК аналитики Excel не отправляется.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    ws["A1"] = "Отчет по инспекции корпусов"
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:F1")
    ws["A1"].alignment = Alignment(horizontal="center")

    ws["A2"] = "Время начала инспекции:"
    ws["B2"] = data.get("Start time", "")

    ws["A3"] = "Время окончания инспекции:"
    ws["B3"] = data.get("Finish time", "")

    defects = data.get("defects", [])
    total_items = len(defects)
    good_count = sum(1 for item in defects if item.get("type") == "good")
    defective_count = total_items - good_count

    ws["D2"] = "Годных корпусов:"
    ws["E2"] = good_count
    ws["D3"] = "Бракованных корпусов:"
    ws["E3"] = defective_count

    ws["A6"] = "Детальный отчёт"
    ws["A6"].font = Font(bold=True, size=12)
    ws.merge_cells("A6:F6")

    headers = [
        "Номер корпуса на паллете",
        "Положение по вертикали",
        "Положение по горизонтали",
        "Годность корпуса",
        "Причина брака",
        "Время инспекции",
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")

    defect_type_mapping = {
        "good": "Годен",
        "omission": "Опущение",
        "sinks": "Раковины",
        "platform": "Залив монтажки",
        "contact_overflow": "Залив контактов",
        "contacts": "Залив контактов",
        "contacts_short": "Залив контактов",
        "flatness": "Неплоскостность",
        "glass": "Стекло",
        "mechanics": "Механика ободка",
    }

    for row_num, item in enumerate(defects, start=8):
        ws.cell(row=row_num, column=1, value=row_num - 7)
        ws.cell(row=row_num, column=2, value=int(item.get("vert", 0)) + 1)
        ws.cell(row=row_num, column=3, value=int(item.get("hor", 0)) + 1)

        t = item.get("type", "")
        if t == "good":
            ws.cell(row=row_num, column=4, value="Годен")
            ws.cell(row=row_num, column=5, value="Нет")
        else:
            ws.cell(row=row_num, column=4, value="Брак")
            reason = defect_type_mapping.get(t, t)
            ws.cell(row=row_num, column=5, value=reason)

        ws.cell(row=row_num, column=6, value=item.get("time", ""))

    # Автоширина столбцов
    for col_num in range(1, 7):
        column_letter = get_column_letter(col_num)
        max_length = 0
        for row_num in range(7, 7 + len(defects) + 1):
            v = ws.cell(row=row_num, column=col_num).value
            if v is not None:
                max_length = max(max_length, len(str(v)))
        ws.column_dimensions[column_letter].width = max_length + 2

    # Центрирование строк данных
    for row_num in range(8, 8 + len(defects)):
        for col_num in range(1, 7):
            ws.cell(row=row_num, column=col_num).alignment = Alignment(horizontal="center")

    formatted_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_fname = f"Отчет_{formatted_time}.xlsx"

    # 1) Сохранить Excel в проект
    output_path_in_project = os.path.join("project/configuration/protocols/excel", output_fname)
    os.makedirs(os.path.dirname(output_path_in_project), exist_ok=True)
    wb.save(output_path_in_project)

    # 2) Сохранить локально на рабочий стол
    os.makedirs(LOCAL_EXCEL_DIR, exist_ok=True)
    local_excel_path = os.path.join(LOCAL_EXCEL_DIR, output_fname)
    wb.save(local_excel_path)

    send_consoles_data(
        f"Excel-отчёт сохранен локально: {local_excel_path}",
        "info",
        "green"
    )
