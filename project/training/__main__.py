"""Запуск: python -m project.training (из корня репозитория)."""
import argparse
import webbrowser

import uvicorn

from project.training.collector import TrainingCollector, TrainingConfig
from project.training.server import create_app
from project.training.station import PlanarCameraSource, PlanarMotion


def main(argv=None):
    parser = argparse.ArgumentParser(description="Мастер сбора датасета планарной станции")
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8010)
    parser.add_argument('--root', default='training_datasets')
    parser.add_argument('--serial-port', help='COM-порт; по умолчанию определяется как в основном проекте')
    parser.add_argument('--motion', choices=('on', 'off'), default='on',
                        help='off: робот не перемещается, оператор позиционирует его вручную')
    parser.add_argument('--open-browser', action='store_true')
    args = parser.parse_args(argv)
    cameras = PlanarCameraSource()
    connection = None
    motion = None
    try:
        if args.motion == 'on':
            import serial
            from project.station.connection import defining_presets
            from project.station.requests import move_to_home, move_to_coordinates
            from project.station.modules.algorithms import moving_first_cell
            from project.configuration.coordinates.reading_and_writing_coordinate_configuration import reading_coordinate_configuration
            port, baudrate, timeout = defining_presets()
            port = args.serial_port or port
            if not port:
                parser.error('Контроллер не найден; укажите --serial-port или --motion off')
            connection = serial.Serial(port, baudrate, timeout=timeout)
            motion = PlanarMotion(connection, move_to_home, moving_first_cell,
                                  reading_coordinate_configuration, move_to_coordinates)
        collector = TrainingCollector(TrainingConfig(root_folder=args.root), frame_source=cameras, motion=motion)
        print('Остановите основную программу. При начале первой детали выполняется калибровка и движение к первой ячейке.' if motion else 'Ручное позиционирование: движение робота отключено.')
        if args.open_browser:
            webbrowser.open(f'http://127.0.0.1:{args.port}/')
        uvicorn.run(create_app(collector), host=args.host, port=args.port, log_level='info')
    finally:
        cameras.close()
        if connection is not None:
            connection.close()


if __name__ == '__main__':
    main()
