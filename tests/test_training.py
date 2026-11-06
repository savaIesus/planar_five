import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from project.training.collector import TrainingCollector, TrainingConfig, CollectorError
from project.training.server import create_app
from project.training.station import PlanarMotion, PlanarCameraSource


class MotionTest(unittest.TestCase):
    def setUp(self):
        self.coords = dict(x=6.3, y=53.5, z=1.0)
        self.moves = []
        self.homed = 0
        def home(_):
            self.homed += 1
        def first(_):
            self.coords.update(x=6.3, y=53.5, z=1.0)
        def read(_):
            return self.coords.copy()
        def move(_, x, y, z):
            self.moves.append((round(x, 1), round(y, 1), z))
            self.coords.update(x=round(x, 1), y=round(y, 1), z=z)
        self.motion = PlanarMotion(None, home, first, read, move)

    def test_grid_and_limit(self):
        positions = [self.motion.move_next() for _ in range(100)]
        self.assertEqual(self.homed, 1)
        self.assertEqual((positions[0]['row'], positions[0]['column']), (1, 1))
        self.assertEqual((positions[9]['row'], positions[9]['column']), (1, 10))
        self.assertEqual((positions[10]['row'], positions[10]['column']), (2, 10))
        self.assertEqual((positions[19]['row'], positions[19]['column']), (2, 1))
        self.assertEqual(self.moves[0], (25.0, 53.5, 1.0))
        self.assertEqual(self.moves[9], (174.6, 72.7, 1.0))
        self.assertEqual(len(self.moves), 99)
        with self.assertRaisesRegex(RuntimeError, '100'):
            self.motion.move_next()
        self.assertEqual(len(self.moves), 99)

    def test_failure_latches(self):
        self.motion.move_next()
        self.motion.move = lambda *args: (_ for _ in ()).throw(OSError('link'))
        with self.assertRaises(OSError): self.motion.move_next()
        with self.assertRaisesRegex(RuntimeError, 'неизвестно'): self.motion.move_next()
        with self.assertRaises(RuntimeError): self.motion.reset_session()

    def test_homing_failure_blocks_first_cell(self):
        self.motion.home = lambda _: (_ for _ in ()).throw(TimeoutError())
        with self.assertRaises(TimeoutError): self.motion.move_next()
        self.assertEqual(self.motion.index, 0)
        self.assertTrue(self.motion.failed)


class CollectorTest(unittest.TestCase):
    def test_workflow_and_export(self):
        class Camera:
            def capture_single(self, role): return np.zeros((32, 32, 3), dtype=np.uint8)
        class Motion:
            count = 0
            def reset_session(self): self.count = 0
            def move_next(self):
                self.count += 1
                return {'row': 1, 'column': self.count, 'coordinates': {'x': 1, 'y': 2, 'z': 3}}
            def invalidate(self): raise AssertionError()
        with tempfile.TemporaryDirectory() as root:
            motion = Motion()
            c = TrainingCollector(TrainingConfig(root_folder=root, camera_roles=('CAMERA_0', 'CAMERA_4')), frame_source=Camera(), motion=motion)
            with TestClient(create_app(c)) as client:
                self.assertEqual(client.post('/api/training/session', json={}).status_code, 200)
                part = client.post('/api/training/parts', json={}).json()['part']
                self.assertEqual(part['position']['column'], 1)
                self.assertEqual(client.post('/api/training/parts', json={}).status_code, 409)
                self.assertEqual(motion.count, 1)
                for role in ('CAMERA_0', 'CAMERA_4'):
                    frame = client.post('/api/training/capture', json={})
                    self.assertEqual(frame.status_code, 200, frame.text)
                    self.assertEqual(frame.json()['frame']['camera_role'], role)
                    response = client.post('/api/training/skip', json={})
                    self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(client.post('/api/training/parts/finish', json={}).status_code, 200)
                self.assertEqual(motion.count, 1)
                self.assertEqual(client.post('/api/training/session/finish', json={}).status_code, 200)

    def test_motion_failure_does_not_create_part(self):
        class BadMotion:
            def reset_session(self): pass
            def move_next(self): raise RuntimeError('failure')
        with tempfile.TemporaryDirectory() as root:
            c = TrainingCollector(TrainingConfig(root_folder=root), motion=BadMotion())
            c.start_session()
            with self.assertRaises(CollectorError): c.begin_part()
            self.assertEqual(c.store.part_count, 0)

    def test_camera_release_on_failure(self):
        class Capture:
            released = False
            def isOpened(self): return True
            def read(self): return False, None
            def release(self): self.released = True
        camera = Capture()
        with patch('cv2.VideoCapture', return_value=camera):
            with self.assertRaises(RuntimeError): PlanarCameraSource().capture_single('CAMERA_4')
        self.assertTrue(camera.released)


if __name__ == '__main__': unittest.main()
