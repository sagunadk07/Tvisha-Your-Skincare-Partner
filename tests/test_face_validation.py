import os
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

import face_validation

TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "test-images", "1.png")


def make_gray_solid(value, size=(200, 200)):
    return np.full(size, value, dtype=np.uint8)


def make_gray_checkerboard(size=(200, 200)):
    img = np.zeros(size, dtype=np.uint8)
    img[::2, ::2] = 255
    img[1::2, 1::2] = 255
    return img


def make_rgb_checkerboard(size=(200, 200)):
    """Sharp (high-variance) + mid brightness, so it passes both the blur and brightness
    gates and reaches the face-detection step - used by the validate_and_crop_face tests."""
    arr = np.zeros((*size, 3), dtype=np.uint8)
    arr[::2, ::2] = 200
    arr[1::2, 1::2] = 100
    return Image.fromarray(arr, mode="RGB")


class TestIsTooBlurry:
    def test_flat_image_is_blurry(self):
        # zero variance everywhere - the blurriest possible input
        # (is_too_blurry returns a numpy bool, not a Python bool, hence a truthy assert
        # rather than `is True`)
        assert face_validation.is_too_blurry(make_gray_solid(128))

    def test_high_contrast_checkerboard_is_not_blurry(self):
        assert not face_validation.is_too_blurry(make_gray_checkerboard())


class TestIsBadBrightness:
    def test_too_dark(self):
        result = face_validation.is_bad_brightness(make_gray_solid(10))
        assert result is not None
        assert "too dark" in result.lower()

    def test_too_bright(self):
        result = face_validation.is_bad_brightness(make_gray_solid(250))
        assert result is not None
        assert "bright" in result.lower()

    def test_mid_brightness_is_fine(self):
        assert face_validation.is_bad_brightness(make_gray_solid(128)) is None

    def test_boundary_just_below_min_is_rejected(self):
        gray = make_gray_solid(face_validation.MIN_BRIGHTNESS - 1)
        assert face_validation.is_bad_brightness(gray) is not None

    def test_boundary_at_min_is_accepted(self):
        gray = make_gray_solid(face_validation.MIN_BRIGHTNESS)
        assert face_validation.is_bad_brightness(gray) is None

    def test_boundary_at_max_is_accepted(self):
        gray = make_gray_solid(face_validation.MAX_BRIGHTNESS)
        assert face_validation.is_bad_brightness(gray) is None

    def test_boundary_just_above_max_is_rejected(self):
        gray = make_gray_solid(face_validation.MAX_BRIGHTNESS + 1)
        assert face_validation.is_bad_brightness(gray) is not None


class TestValidateAndCropFace:
    def test_blurry_photo_rejected_before_face_detection_runs(self):
        flat_image = Image.fromarray(np.full((200, 200, 3), 128, dtype=np.uint8), mode="RGB")
        result_image, error = face_validation.validate_and_crop_face(flat_image)
        assert result_image is None
        assert "blurry" in error.lower()

    @patch("face_validation.FACE_DETECTOR")
    def test_no_face_detected_returns_the_full_uncropped_image(self, mock_face_detector):
        mock_face_detector.detectMultiScale.return_value = np.empty((0, 4), dtype=int)
        img = make_rgb_checkerboard()
        result_image, error = face_validation.validate_and_crop_face(img)
        assert error is None
        assert result_image is not None
        assert result_image.size == img.size

    @patch("face_validation.EYE_DETECTOR")
    @patch("face_validation.FACE_DETECTOR")
    def test_single_face_with_an_eye_gets_cropped(self, mock_face_detector, mock_eye_detector):
        mock_face_detector.detectMultiScale.return_value = np.array([[50, 50, 80, 80]])
        mock_eye_detector.detectMultiScale.return_value = np.array([[10, 10, 15, 15]])
        img = make_rgb_checkerboard()
        result_image, error = face_validation.validate_and_crop_face(img)
        assert error is None
        assert result_image is not None
        assert result_image.size != img.size

    @patch("face_validation.EYE_DETECTOR")
    @patch("face_validation.FACE_DETECTOR")
    def test_face_region_without_an_eye_is_not_treated_as_a_real_face(
        self, mock_face_detector, mock_eye_detector
    ):
        # detectMultiScale found *something* face-shaped, but no eye inside it - the function
        # is deliberately written to treat that as a false positive, not a real face
        mock_face_detector.detectMultiScale.return_value = np.array([[50, 50, 80, 80]])
        mock_eye_detector.detectMultiScale.return_value = np.empty((0, 4), dtype=int)
        img = make_rgb_checkerboard()
        result_image, error = face_validation.validate_and_crop_face(img)
        assert error is None
        assert result_image.size == img.size

    @patch("face_validation.EYE_DETECTOR")
    @patch("face_validation.FACE_DETECTOR")
    def test_multiple_real_faces_are_rejected(self, mock_face_detector, mock_eye_detector):
        mock_face_detector.detectMultiScale.return_value = np.array(
            [[10, 10, 60, 60], [100, 100, 60, 60]]
        )
        mock_eye_detector.detectMultiScale.return_value = np.array([[5, 5, 10, 10]])
        img = make_rgb_checkerboard()
        result_image, error = face_validation.validate_and_crop_face(img)
        assert result_image is None
        assert "multiple faces" in error.lower()


@pytest.mark.skipif(not os.path.exists(TEST_IMAGE_PATH), reason="test-images/1.png not present")
def test_real_photo_end_to_end_does_not_crash():
    """One non-mocked test against a real photo, so the mocked unit tests above aren't the
    only thing standing between this module and a real OpenCV/Haar-cascade regression."""
    img = Image.open(TEST_IMAGE_PATH)
    result_image, error = face_validation.validate_and_crop_face(img)
    assert error is None
    assert result_image is not None
