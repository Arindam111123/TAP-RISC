"""
test_sensors.py
===============
Unit tests for sensors and the 2-of-3 fusion voter.
"""
import unittest

from simulator.sensors import (
    MPU6050, BMP280, CapacitiveMesh,
    fuse, SensorState, SensorReading,
)


class TestMPU6050(unittest.TestCase):
    def test_resting_is_normal(self):
        m = MPU6050()
        for t in range(10):
            r = m.read(t * 0.01)
            self.assertEqual(r.state, SensorState.NORMAL)

    def test_shock_triggers_tamper(self):
        m = MPU6050(shock_g=2.0)
        m.apply_shock(magnitude_g=5.0, duration_s=0.1, fs=100)
        # consume the first shock sample
        r = m.read(0.0)
        self.assertEqual(r.state, SensorState.TAMPERED)

    def test_tamper_state_latches(self):
        m = MPU6050(shock_g=2.0)
        m.apply_shock(magnitude_g=5.0, duration_s=0.01, fs=100)
        m.read(0.0)
        # Even after the queue is drained, state must remain TAMPERED.
        for _ in range(10):
            r = m.read(0.1)
            self.assertEqual(r.state, SensorState.TAMPERED)


class TestBMP280(unittest.TestCase):
    def test_steady_is_normal(self):
        b = BMP280()
        for i in range(50):
            r = b.read(i * 0.01)
        self.assertEqual(r.state, SensorState.NORMAL)

    def test_breach_triggers(self):
        b = BMP280(breach_delta_hpa=4.0)
        # Build up some history first
        for i in range(20):
            b.read(i * 0.01)
        b.apply_breach(delta_hpa=-10.0)
        triggered = False
        for i in range(20, 50):
            r = b.read(i * 0.01)
            if r.state == SensorState.TAMPERED:
                triggered = True
                break
        self.assertTrue(triggered)


class TestCapacitiveMesh(unittest.TestCase):
    def test_intact_is_normal(self):
        c = CapacitiveMesh()
        r = c.read(0.0)
        self.assertEqual(r.state, SensorState.NORMAL)

    def test_cut_triggers_tamper(self):
        c = CapacitiveMesh()
        c.apply_cut()
        r = c.read(0.0)
        self.assertEqual(r.state, SensorState.TAMPERED)


class TestFusion(unittest.TestCase):
    def _reading(self, channel: str, state: SensorState) -> SensorReading:
        return SensorReading(t=0.0, value=0.0, channel=channel, state=state)

    def test_two_of_three_triggers(self):
        d = fuse([
            self._reading("mpu6050", SensorState.TAMPERED),
            self._reading("bmp280",  SensorState.TAMPERED),
            self._reading("mesh",    SensorState.NORMAL),
        ])
        self.assertTrue(d.tampered)
        self.assertEqual(d.n_tampered, 2)

    def test_one_of_three_does_not_trigger(self):
        d = fuse([
            self._reading("mpu6050", SensorState.TAMPERED),
            self._reading("bmp280",  SensorState.NORMAL),
            self._reading("mesh",    SensorState.NORMAL),
        ])
        self.assertFalse(d.tampered)

    def test_all_normal(self):
        d = fuse([
            self._reading("mpu6050", SensorState.NORMAL),
            self._reading("bmp280",  SensorState.NORMAL),
            self._reading("mesh",    SensorState.NORMAL),
        ])
        self.assertFalse(d.tampered)


if __name__ == "__main__":
    unittest.main()
