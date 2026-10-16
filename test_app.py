import threading
import unittest
from unittest.mock import MagicMock, call, patch

import cv2
import numpy as np

from app import app
from visionlogix.camera import CameraService, open_camera


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_renders_stage_one_interface(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"STAGE 01", response.data)
        self.assertIn(b"DETECTED MARKERS", response.data)

    def test_status_endpoint_reports_camera_initially_off(self):
        response = self.client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["running"])

    def test_marker_endpoint_returns_png_and_rejects_unsupported_id(self):
        valid = self.client.get("/api/marker/7.png")
        invalid = self.client.get("/api/marker/50.png")

        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.mimetype, "image/png")
        self.assertTrue(valid.data.startswith(b"\x89PNG"))
        self.assertEqual(invalid.status_code, 400)


class CameraBackendTests(unittest.TestCase):
    @patch("visionlogix.camera.platform.system", return_value="Windows")
    @patch("visionlogix.camera.cv2.VideoCapture")
    def test_uses_directshow_on_windows(self, video_capture, _system):
        capture = MagicMock()
        capture.isOpened.return_value = True
        video_capture.return_value = capture

        result, backend = open_camera(0)

        self.assertIs(result, capture)
        self.assertEqual(backend, "DirectShow")
        video_capture.assert_called_once_with(0, cv2.CAP_DSHOW)

    @patch("visionlogix.camera.platform.system", return_value="Windows")
    @patch("visionlogix.camera.cv2.VideoCapture")
    def test_falls_back_when_directshow_is_unavailable(self, video_capture, _system):
        directshow = MagicMock()
        directshow.isOpened.return_value = False
        default = MagicMock()
        default.isOpened.return_value = True
        video_capture.side_effect = [directshow, default]

        result, backend = open_camera(2)

        self.assertIs(result, default)
        self.assertEqual(backend, "default")
        directshow.release.assert_called_once()
        self.assertEqual(video_capture.call_args_list, [
            call(2, cv2.CAP_DSHOW),
            call(2),
        ])

    @patch("visionlogix.camera.open_camera")
    def test_camera_is_opened_read_and_released_on_worker_thread(self, mock_open):
        frame = np.full((120, 160, 3), 255, dtype=np.uint8)
        open_thread_ids = []
        read_thread_ids = []
        release_thread_ids = []
        capture = MagicMock()

        def fake_open(_index):
            open_thread_ids.append(threading.get_ident())
            return capture, "test backend"

        def fake_read():
            read_thread_ids.append(threading.get_ident())
            return True, frame

        mock_open.side_effect = fake_open
        capture.read.side_effect = fake_read
        capture.release.side_effect = lambda: release_thread_ids.append(threading.get_ident())

        service = CameraService()
        try:
            started, _ = service.start()

            self.assertTrue(started)
            self.assertTrue(read_thread_ids)
            self.assertTrue(all(
                thread_id == open_thread_ids[0]
                for thread_id in read_thread_ids
            ))
        finally:
            service.stop()

        self.assertEqual(release_thread_ids, [open_thread_ids[0]])

    def test_video_feed_returns_clear_error_if_camera_is_not_running(self):
        response = app.test_client().get("/video_feed")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "Camera is not ready to stream frames.")


if __name__ == "__main__":
    unittest.main()
