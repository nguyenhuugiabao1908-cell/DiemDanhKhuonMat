# utils/face_encoder.py

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import face_recognition
import numpy as np

from utils.database import DatabaseManager
from utils.helpers import logger


class FaceEncoder:
    """
    Face encoding manager.
    """

    def __init__(self) -> None:
        self.db = DatabaseManager()

    # ---------------------------------------------------------

    def get_face_encoding(
        self,
        image: np.ndarray,
    ) -> Optional[np.ndarray]:
        """
        Extract face encoding from image.
        """

        try:

            if image is None:
                return None

            rgb = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB,
            )

            locations = face_recognition.face_locations(rgb)

            if len(locations) == 0:
                return None

            encodings = face_recognition.face_encodings(
                rgb,
                locations,
            )

            if not encodings:
                return None

            return encodings[0]

        except Exception as exc:
            logger.exception(exc)
            return None

    # ---------------------------------------------------------

    def save_encoding(
        self,
        student_id: str,
        encoding: np.ndarray,
        image_path: str = "",
    ) -> bool:
        """
        Save encoding into database.
        """

        try:

            return self.db.save_encoding(
                student_id=student_id,
                encoding=encoding,
                image_path=image_path,
            )

        except Exception as exc:
            logger.exception(exc)
            return False

    # ---------------------------------------------------------

    def load_all_encodings(
        self,
    ) -> Tuple[List[np.ndarray], List[str]]:
        """
        Load all face encodings.
        """

        known_encodings: List[np.ndarray] = []
        known_student_ids: List[str] = []

        try:

            rows = self.db.load_encodings()

            for row in rows:

                known_student_ids.append(
                    row["student_id"]
                )

                known_encodings.append(
                    row["encoding"]
                )

            logger.info(
                "Loaded %d face encodings.",
                len(known_student_ids),
            )

        except Exception as exc:
            logger.exception(exc)

        return known_encodings, known_student_ids

    # ---------------------------------------------------------

    def reload(self) -> Tuple[List[np.ndarray], List[str]]:
        """
        Alias of load_all_encodings().
        """

        return self.load_all_encodings()

    # ---------------------------------------------------------

    def total_faces(self) -> int:
        """
        Total registered faces.
        """

        return len(
            self.db.load_encodings()
        )