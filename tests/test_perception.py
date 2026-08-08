import unittest

import numpy as np

from geekseek.perception import (
    FakePersonSensor,
    PersonSignal,
    center_crop_to_aspect,
    is_approaching,
    is_positioned,
)


class PerceptionTests(unittest.TestCase):
    def test_fake_sensor_replays_scripted_signals(self) -> None:
        sensor = FakePersonSensor(
            [PersonSignal(detected=False), PersonSignal(detected=True, size_ratio=0.2)]
        )
        self.assertFalse(sensor.sense(None).detected)
        self.assertTrue(sensor.sense(None).detected)

    def test_fake_sensor_repeats_last_signal(self) -> None:
        sensor = FakePersonSensor([PersonSignal(detected=True, size_ratio=0.5)])
        sensor.sense(None)
        second = sensor.sense(None)
        self.assertEqual(second.size_ratio, 0.5)

    def test_is_approaching_requires_detection_and_size(self) -> None:
        self.assertFalse(is_approaching(PersonSignal(detected=False, size_ratio=0.9)))
        self.assertFalse(is_approaching(PersonSignal(detected=True, size_ratio=0.05)))
        self.assertTrue(is_approaching(PersonSignal(detected=True, size_ratio=0.2)))

    def test_is_positioned_checks_center_zone(self) -> None:
        centered = PersonSignal(detected=True, center_x=0.5, center_y=0.5)
        off_frame = PersonSignal(detected=True, center_x=0.05, center_y=0.5)
        undetected = PersonSignal(detected=False, center_x=0.5, center_y=0.5)
        self.assertTrue(is_positioned(centered))
        self.assertFalse(is_positioned(off_frame))
        self.assertFalse(is_positioned(undetected))

    def test_center_crop_4_by_3_source_to_3_by_4_without_resize(self) -> None:
        frame = np.zeros((960, 1280, 3), dtype=np.uint8)
        cropped = center_crop_to_aspect(frame, 3, 4)
        self.assertEqual(cropped.shape, (960, 720, 3))
        self.assertTrue(np.shares_memory(frame, cropped))

    def test_center_crop_rejects_invalid_aspect(self) -> None:
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            center_crop_to_aspect(frame, 0, 4)


if __name__ == "__main__":
    unittest.main()
