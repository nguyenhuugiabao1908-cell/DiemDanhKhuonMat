# utils/camera.py

from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np

from utils.helpers import logger


class Camera:
    """
    Thread-safe camera manager.
    """

    def __init__(
        self,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps

        self.capture: Optional[cv2.VideoCapture] = None

        self.frame: Optional[np.ndarray] = None

        self.running = False

        self.lock = threading.Lock()

        self.thread: Optional[threading.Thread] = None

    # --------------------------------------------------

    def open(self) -> bool:
        """
        Open camera.
        """

        if self.capture is not None:
            return True

        self.capture = cv2.VideoCapture(
            self.camera_index,
            cv2.CAP_DSHOW,
        )

        if not self.capture.isOpened():
            logger.error("Cannot open camera.")
            return False

        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            self.width,
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            self.height,
        )

        self.capture.set(
            cv2.CAP_PROP_FPS,
            self.fps,
        )

        logger.info("Camera opened.")

        return True

    # --------------------------------------------------

    def start(self) -> bool:
        """
        Start reading frames.
        """

        if self.running:
            return True

        if not self.open():
            return False

        self.running = True

        self.thread = threading.Thread(
            target=self._update,
            daemon=True,
        )

        self.thread.start()

        logger.info("Camera thread started.")

        return True

    # --------------------------------------------------

    def _update(self) -> None:
        """
        Camera loop.
        """

        while self.running:

            if self.capture is None:
                continue

            success, frame = self.capture.read()

            if not success:
                time.sleep(0.01)
                continue

            with self.lock:
                self.frame = frame.copy()

            time.sleep(1 / self.fps)

    # --------------------------------------------------

    def read(self) -> Optional[np.ndarray]:
        """
        Get latest frame.
        """

        with self.lock:

            if self.frame is None:
                return None

            return self.frame.copy()

    # --------------------------------------------------

    def read_rgb(self) -> Optional[np.ndarray]:
        """
        Return RGB frame.
        """

        frame = self.read()

        if frame is None:
            return None

        return cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

    # --------------------------------------------------

    def save_frame(
        self,
        path: str,
    ) -> bool:
        """
        Save current frame.
        """

        frame = self.read()

        if frame is None:
            return False

        cv2.imwrite(path, frame)

        logger.info("Saved image: %s", path)

        return True

    # --------------------------------------------------

    def stop(self) -> None:
        """
        Stop camera thread.
        """

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1)

        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.frame = None

        logger.info("Camera stopped.")

    # --------------------------------------------------

    def is_opened(self) -> bool:
        if self.capture is None:
            return False

        return self.capture.isOpened()

    # --------------------------------------------------

    def get_resolution(self) -> tuple[int, int]:
        return (
            self.width,
            self.height,
        )

    # --------------------------------------------------

    def set_resolution(
        self,
        width: int,
        height: int,
    ) -> None:

        self.width = width
        self.height = height

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            width,
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            height,
        )

    # --------------------------------------------------

    def __enter__(self):

        self.start()

        return self

    # --------------------------------------------------

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:

        self.stop()

    # Backward compatibility
CameraCapture = Camera