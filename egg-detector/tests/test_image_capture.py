from unittest.mock import MagicMock, patch

import cv2
from PIL import Image
import pytest
from requests import ConnectTimeout

from egg_detector.image_capture import ImageCapture


@pytest.mark.asyncio
class TestImageCapture:
    @patch("requests.post")
    @patch("egg_detector.image_capture.ImageCapture._get_lights_plug")
    @patch("egg_detector.image_capture.CameraWithFocusAndTimeout.get_snap")
    async def test_capture(self, get_snap, get_lights_plug, requests_post):
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.json.return_value = [
            {
                "cmd": "Login",
                "code": 0,
                "value": {"Token": {"leaseTime": 3600, "name": "FAKE_TOKEN"}},
            }
        ]

        zoom_response = MagicMock()
        zoom_response.status_code = 200
        zoom_response.json.return_value = [
            {"cmd": "StartZoomFocus", "code": 0, "value": {"rspCode": 200}}
        ]

        focus_response = MagicMock()
        focus_response.status_code = 200
        focus_response.json.return_value = [
            {"cmd": "StartZoomFocus", "code": 0, "value": {"rspCode": 200}}
        ]

        requests_post.side_effect = [
            login_response,
            zoom_response,
            focus_response,
        ]

        get_snap.return_value = Image.open("test_images/multiple_eggs.jpg")

        image_capture = ImageCapture(
            camera_ip="0.0.0.0",
            lights_plug_ip="0.0.0.1",
            lights_plug_port="0.0.0.2",
        )

        img = await image_capture.capture(use_flash=True)

        get_lights_plug.turn_on.assert_called_once
        get_lights_plug.turn_off.assert_called_once
        assert img is not None

    @patch("requests.post")
    @patch("egg_detector.image_capture.ImageCapture._get_lights_plug")
    async def test_camera_connect_timeout(self, get_lights_plug, requests_post):
        requests_post.side_effect = ConnectTimeout
        image_capture = ImageCapture(
            camera_ip="0.0.0.0",
            lights_plug_ip="0.0.0.1",
            lights_plug_port="0.0.0.2",
        )

        with pytest.raises(ConnectTimeout):
            await image_capture.capture(use_flash=True)
