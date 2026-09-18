# utils/recognizer.py

from __future__ import annotations

from typing import List, Tuple

import cv2
import face_recognition
import numpy as np

from utils.helpers import logger


class Recognizer:
    """
    Face recognition manager.
    """

    SCALE_FACTOR = 0.25
    TOLERANCE = 0.45

    def __init__(
        self,
        known_encodings: List[np.ndarray],
        known_student_ids: List[str],
    ) -> None:
        self.known_encodings = known_encodings
        self.known_student_ids = known_student_ids

        logger.info(
            "Recognizer initialized with %d face encodings.",
            len(self.known_encodings),
        )

    def recognize(
        self,
        frame: np.ndarray,
    ) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
        """
        Detect and recognize faces in a frame.

        Returns:
            [
                (
                    student_id,
                    confidence,
                    (top, right, bottom, left)
                )
            ]
        """

        try:

            if frame is None:
                return []

            small_frame = cv2.resize(
                frame,
                (0, 0),
                fx=self.SCALE_FACTOR,
                fy=self.SCALE_FACTOR,
            )

            rgb_frame = cv2.cvtColor(
                small_frame,
                cv2.COLOR_BGR2RGB,
            )

            face_locations = face_recognition.face_locations(
                rgb_frame
            )

            if not face_locations:
                return []

            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations,
            )

            results = []

            scale = int(1 / self.SCALE_FACTOR)

            for face_encoding, location in zip(
                face_encodings,
                face_locations,
            ):

                student_id = "Unknown"
                confidence = 0.0

                if self.known_encodings:

                    distances = face_recognition.face_distance(
                        self.known_encodings,
                        face_encoding,
                    )

                    best_match = int(np.argmin(distances))

                    matches = face_recognition.compare_faces(
                        self.known_encodings,
                        face_encoding,
                        tolerance=self.TOLERANCE,
                    )

                    if matches[best_match]:

                        student_id = self.known_student_ids[
                            best_match
                        ]

                        distance = float(
                            distances[best_match]
                        )

                        confidence = (
                            1.0 - distance
                        ) * 100

                        confidence = max(
                            0.0,
                            min(100.0, confidence),
                        )

                        confidence = round(
                            confidence,
                            2,
                        )

                top, right, bottom, left = location

                location = (
                    top * scale,
                    right * scale,
                    bottom * scale,
                    left * scale,
                )

                results.append(
                    (
                        student_id,
                        confidence,
                        location,
                    )
                )

            return results

        except Exception as exc:
            logger.exception(exc)
            return []

    def update_database(
        self,
        known_encodings: List[np.ndarray],
        known_student_ids: List[str],
    ) -> None:
        """
        Reload face encodings without restarting program.
        """

        self.known_encodings = known_encodings
        self.known_student_ids = known_student_ids

        logger.info(
            "Recognizer database updated (%d faces).",
            len(self.known_encodings),
        )

    def total_faces(self) -> int:
        """
        Return total registered faces.
        """

        return len(self.known_encodings)

