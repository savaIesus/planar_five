"""Адаптеры камер и перемещений существующей планарной станции."""
from project.training.collector import DEFAULT_CAMERA_ROLES


class PlanarCameraSource:
    def capture_single(self, role):
        if role not in DEFAULT_CAMERA_ROLES:
            raise ValueError(f"Неизвестная камера: {role}")
        import cv2
        index = DEFAULT_CAMERA_ROLES.index(role)
        camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        try:
            if not camera.isOpened():
                raise RuntimeError(f"Камера {index} не открылась")
            # Новое подключение не содержит кадров предыдущей ячейки.
            for _ in range(5):
                ok, frame = camera.read()
                if not ok or frame is None:
                    raise RuntimeError(f"Камера {index} не возвращает кадры")
            return frame
        finally:
            camera.release()

    def close(self):
        pass


class PlanarMotion:
    """Первая ячейка после калибровки, далее змейка как в algorithms.py.

    После ошибки позиция неизвестна: повторное движение запрещено до перезапуска
    программы и проверки установки оператором.
    """
    def __init__(self, connection, home, first_cell, read_coordinates, move):
        self.connection = connection
        self.home = home
        self.first_cell = first_cell
        self.read_coordinates = read_coordinates
        self.move = move
        self.failed = False
        self.index = 0

    def invalidate(self):
        self.failed = True

    def reset_session(self):
        if self.failed:
            raise RuntimeError("Положение робота неизвестно; проверьте установку и перезапустите мастер")
        self.index = 0

    def move_next(self):
        if self.failed:
            raise RuntimeError("Положение робота неизвестно; проверьте установку и перезапустите мастер")
        if self.index >= 100:
            raise RuntimeError("Все 100 ячеек пройдены")
        row, step = divmod(self.index, 10)
        column = step if row % 2 == 0 else 9 - step
        try:
            if self.index == 0:
                self.home(self.connection)
                self.first_cell(self.connection)
            else:
                coordinates = self.read_coordinates('relevant_coordinates.json')
                x, y, z = (coordinates[key] for key in ('x', 'y', 'z'))
                if step == 0:
                    y += 19.2
                else:
                    x += 18.7 if row % 2 == 0 else -18.7
                self.move(self.connection, x, y, z)
            coordinates = self.read_coordinates('relevant_coordinates.json')
        except Exception:
            self.failed = True
            raise
        self.index += 1
        return {"row": row + 1, "column": column + 1,
                "coordinates": {key: coordinates[key] for key in ('x', 'y', 'z')}}
