from pathlib import Path
from ultralytics import YOLO

print("Текущая рабочая папка:", Path.cwd())

project_root = Path(__file__).resolve().parent.parent
print("Корень проекта:", project_root)

weights = [
    "project/station/weights/steklo12n.pt",
    "project/station/weights/top_sink.pt",
    "project/station/weights/side_flatness_short.pt",
    "project/station/weights/top_mechanics.pt",
    "project/station/weights/bottom_glass.pt",
    "project/station/weights/top_platform.pt",
    "project/station/weights/top_contacts.pt",
    "project/station/weights/side_omission_x.pt",
    "project/station/weights/top_or_bot_side_y.pt",
    "project/station/weights/top_or_bot_side_x.pt",
    "project/station/weights/side_omission_long.pt",
    "project/station/weights/bottom_welding.pt",
]

for rel_path in weights:
    full_path = project_root / rel_path

    print("\nПроверяю:", full_path)

    if not full_path.exists():
        print("ОШИБКА: файла нет")
        continue

    print("Файл найден, размер:", full_path.stat().st_size, "байт")

    try:
        model = YOLO(str(full_path))
        print("OK: модель загрузилась")
    except Exception as e:
        print("ОШИБКА ЗАГРУЗКИ:")
        print(e)