import os
import cv2
import numpy
from flet import colors
from ultralytics import YOLO

from project.application.modules.together import send_consoles_data
from project.station.modules.math import bounding_rectangular, text_placement


def uploading_a_neural_network_model(model_path):
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Модель не найдена по пути: {model_path}")

    weight = YOLO(model_path)
    weight.fuse()

    return weight


def process_frame(frame, model, conf=0.3, draw_area=0):
    """
    Обрабатывает кадр, применяя модель для обнаружения объектов, и возвращает кадр
    с наложенными полигонами, а также список объектов с их названиями, классами,
    площадями, центрами масс и средними значениями пикселей.

    Параметры:
    frame (numpy.ndarray): Кадр изображения.
    Model: Модель для предсказания объектов.
    Draw_area (int):
        Флаг для управления отображением площади на кадре (0 - не рисовать, 1 - рисовать).

    Возвращает:
    tuple:
        - numpy.ndarray: Обработанный кадр.
        - list: Список объектов в формате
          [{"name": str, "class": int, "area": float,
            "center": (int, int), "mean_pixel_value": float}].
    """
    results_detect = model.predict(
        frame, iou=0.5, conf=conf, imgsz=640, verbose=False, task="segment") # было iou=0

    object_data = []

    if results_detect[0].masks is not None and len(results_detect[0].masks.xy) > 0:
        masks = results_detect[0].masks
        segments = masks.xy
        classes = results_detect[0].boxes.cls.cpu().numpy().astype(int)
        names = results_detect[0].names
        print(names)

        y_max_global = float('-inf')
        y_min_global = float('inf')

        for segment, clss in zip(segments, classes):
            if len(segment) > 0:
                contour_color = (0, 255, 0)
                segment = segment.astype(int)

                # Рисуем контур сегмента
                cv2.polylines(frame, [segment], isClosed=True, color=contour_color, thickness=2)
                area = cv2.contourArea(segment)

                # Создаем бинарную маску для сегмента
                mask = numpy.zeros(frame.shape[:2], dtype=numpy.uint8)
                cv2.drawContours(mask, [segment], -1, 255, thickness=cv2.FILLED)

                # Вычисляем среднее значение пикселей внутри маски
                mean_pixel_value = cv2.mean(
                    frame, mask=mask)[:3]  # Берем только BGR (первые 3 канала)

                distance = None
                moment = cv2.moments(segment)
                if names[clss] == "Omission" or names[clss] == "omission":
                    distance = bounding_rectangular(y_max_global, y_min_global, segment, frame)

                text_placement(moment, draw_area, area, frame)

                # Добавляем среднее значение пикселей в object_info
                object_info = {
                    "class_name": names[clss],
                    "distance": distance,
                    "segment": segment.tolist(),
                    "area": cv2.contourArea(segment),
                    "mean_pixel_value": mean_pixel_value  # Среднее значение пикселей
                }
                object_data.append(object_info)

        if object_data:
            send_consoles_data("Обнаруженные объекты:")

            for i, obj in enumerate(object_data):
                if i == len(object_data) - 1:
                    send_consoles_data(f"{obj['class_name']} \n", "console", colors.ORANGE)
                else:
                    send_consoles_data(f"{obj['class_name']}", "console", colors.ORANGE)

    return frame, object_data


def process_frame_alt(frame, model, conf=0.3, draw_area=0):
    """
    Обрабатывает кадр, применяя модель для обнаружения объектов, и возвращает кадр
    с наложенными bounding box'ами, а также список объектов с их названиями, классами,
    площадями, центрами масс и средними значениями пикселей.

    Параметры:
    frame (numpy.ndarray): Кадр изображения.
    model: Модель для предсказания объектов (YOLOv8/v9/v10).
    conf (float): Порог уверенности модели.
    draw_area (int): Флаг для управления отображением площади на кадре (0 - не рисовать, 1 - рисовать).

    Возвращает:
    tuple:
        - numpy.ndarray: Обработанный кадр.
        - list: Список объектов в формате
          [{"name": str, "class": int, "area": float,
            "center": (int, int), "mean_pixel_value": float}].
    """
    results_detect = model.predict(
        frame, iou=0.5, conf=conf, imgsz=1024, verbose=False, task="detection"
    )

    object_data = []

    # Проверяем наличие детекций (bounding boxes) вместо масок
    if results_detect[0].boxes is not None and len(results_detect[0].boxes) > 0:
        boxes = results_detect[0].boxes.xyxy.cpu().numpy()  # Формат: [x1, y1, x2, y2]
        classes = results_detect[0].boxes.cls.cpu().numpy().astype(int)
        names = results_detect[0].names

        y_max_global = float('-inf')
        y_min_global = float('inf')

        for box, clss in zip(boxes, classes):
            x1, y1, x2, y2 = map(int, box)

            # Валидация координат
            if x2 <= x1 or y2 <= y1:
                continue

            # 1. Рисуем bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 2. Вычисляем площадь и центр
            area = (x2 - x1) * (y2 - y1)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # 3. Среднее значение пикселей внутри бокса (через ROI, быстрее чем маска)
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                mean_bgr = cv2.mean(roi)[:3]
                mean_pixel_value = float(numpy.mean(mean_bgr))  # Усредняем BGR в одно число
            else:
                mean_pixel_value = 0.0

            # 4. Обновляем глобальные границы Y (исправлен баг оригинала)
            if y2 > y_max_global: y_max_global = y2
            if y1 < y_min_global: y_min_global = y1

            distance = None
            class_name = names[clss]

            # Проверка класса (регистронезависимая)
            if class_name.lower() in ["omission", "omission_short"]:
                # Передаем координаты бокса вместо полигона
                distance = bounding_rectangular(y_max_global, y_min_global, box, frame)

            # Подготовка моментов для совместимости с text_placement
            # (эмуляция cv2.moments для прямоугольника)
            moment = {"m00": area, "m10": area * cx, "m01": area * cy}
            text_placement(moment, draw_area, area, frame)

            # Формируем словарь объекта согласно docstring
            object_info = {
                "name": class_name,
                "class_name": class_name,  # ← алиас для обратной совместимости
                "class": int(clss),
                "area": float(area),
                "center": (cx, cy),
                "mean_pixel_value": mean_pixel_value,
                "bbox": [x1, y1, x2, y2]  # Добавлено для отладки/расширения
            }
            object_data.append(object_info)

        # Вывод в консоль
        if object_data:
            send_consoles_data("Обнаруженные объекты:")
            for i, obj in enumerate(object_data):
                suffix = " \n" if i == len(object_data) - 1 else ""
                send_consoles_data(f"{obj['name']}{suffix}", "console", colors.ORANGE)

    return frame, object_data
