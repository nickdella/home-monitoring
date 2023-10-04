import time
from typing import Dict

import cv2
import kasa
import numpy as np
import requests
import reolinkapi
from reolinkapi.handlers.rest_handler import Request

from egg_detector import logger, secrets


logger = logger.get(__name__)


class ImageCapture:
    def __init__(self, camera_ip, lights_plug_ip=None, lights_plug_port=None):
        self.camera_ip = camera_ip

        self.lights_plug_ip = lights_plug_ip
        self.lights_plug_port = lights_plug_port
        self.lights_plug = None

    async def capture(self, use_flash=False):
        # Use Kasa API to turn on spotlights
        if use_flash:
            plug = await self._get_lights_plug()
            await plug.turn_on()
            logger.info("Turned flash on")

        try:
            # Take snapshot and save to local file
            camera = CameraWithFocusAndTimeout(
                ip=self.camera_ip,
                https=True,
                username=secrets.REOLINK_USERNAME,
                password=secrets.REOLINK_PASSWORD,
                defer_login=True,
            )

            timeout = (5, 5)
            logger.info("Logging in to camera")
            if not camera.login(timeout=timeout):
                raise Exception("Could not log in to camera")

            # silly camera keeps trying to refocus itself at night
            logger.info("Focusing camera")
            camera.set_zoom(28)
            camera.set_focus(194)
            # wait for focusing to finish
            time.sleep(3)

            logger.info("Downloading image")
            pil_image = camera.get_snap(timeout=timeout)
            np_img = np.array(pil_image)
            cv2_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
            return cv2_img
        finally:
            if use_flash:
                plug = await self._get_lights_plug()
                await plug.turn_off()
                logger.info("Turned flash off")

    async def _get_lights_plug(self):
        if self.lights_plug:
            return self.lights_plug
        else:
            # support either SmartStrip or SmartPlug
            if self.lights_plug_port:
                strip = kasa.smartstrip.SmartStrip(host=self.lights_plug_ip)
                await strip.update()
                plug = strip.children[self.lights_plug_port]
            else:
                plug = kasa.smartplug.SmartPlug(host=self.lights_plug_ip)
                await plug.update()

            self.lights_plug = plug
            return self.lights_plug


class CameraWithFocusAndTimeout(reolinkapi.Camera):
    """We extend the core reolink.Camera class in two ways:

    1. Override reolinkapi.Camera's login() method to allow us to pass a
       connect+read timeout to the underlying Python requests library
    2. Add the StartZoomFocus API, which was introduced in API v1.5
    """

    def login(self, timeout: (int, int)):
        try:
            body = [
                {
                    "cmd": "Login",
                    "action": 0,
                    "param": {
                        "User": {"userName": self.username, "password": self.password}
                    },
                }
            ]
            param = {"cmd": "Login", "token": "null"}
            headers = {"content-type": "application/json"}

            response = requests.post(
                self.url,
                verify=False,
                params=param,
                json=body,
                headers=headers,
                proxies=Request.proxies,
                timeout=timeout,
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Http Request had non-200 Status: {response.status_code}",
                    response.status_code,
                )

            data = response.json()[0]
            code = data["code"]
            if int(code) == 0:
                self.token = data["value"]["Token"]["name"]
                return True

            return False
        except Exception as e:
            raise

    def set_zoom(self, pos):
        resp = self._execute_zoom_focus("ZoomPos", pos)
        self.check_resp(resp)
        return resp

    def set_focus(self, pos):
        resp = self._execute_zoom_focus("FocusPos", pos)
        self.check_resp(resp)
        return resp

    def check_resp(self, resp):
        if not (resp and resp[0]["value"] and resp[0]["value"]["rspCode"] == 200):
            raise Exception("Non-200 response code returned: ", resp)
        else:
            pass

    def _execute_zoom_focus(self, operation: str, pos: int) -> Dict:
        data = [
            {
                "cmd": "StartZoomFocus",
                "action": 0,
                "param": {"ZoomFocus": {"channel": 0, "op": operation, "pos": pos}},
            }
        ]
        return self._execute_command("StartZoomFocus", data)
