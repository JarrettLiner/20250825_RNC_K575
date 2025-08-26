import logging
from time import time

class PowerServo:
    def __init__(self, vsg, pm, vsa, max_iterations=10, tolerance=0.1):
        """
        Initialize PowerServo class for adjusting input power to reach target output.

        Args:
            vsg: VSG instance for setting input power.
            pm: PowerMeter instance for measuring power.
            vsa: VSA instance for setting reference level.
            max_iterations (int): Maximum number of servo iterations.
            tolerance (float): Power tolerance in dB.
        """
        self.vsg = vsg
        self.pm = pm
        self.vsa = vsa
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)

    def servo_power(self, freq_ghz, target_output, expected_gain):
        """
        Adjust input power to achieve target output power.

        Args:
            freq_ghz (float): Frequency in GHz.
            target_output (float): Target output power in dBm.
            expected_gain (float): Expected gain in dB.

        Returns:
            tuple: (servo_iterations, servo_settle_time)
        """
        initial_pwr = target_output - expected_gain
        servo_start_time = time()
        servo_iterations = 0
        servo_settle_time = None

        for i in range(self.max_iterations):
            _, current_output = self.pm.measure()
            servo_iterations = i + 1
            if abs(current_output - target_output) < self.tolerance:
                servo_settle_time = round(time() - servo_start_time, 3)
                self.logger.info(
                    f"Servo converged after {servo_iterations} iterations in {servo_settle_time} s at {freq_ghz} GHz")
                break
            adjustment = target_output - current_output
            initial_pwr += adjustment
            self.vsg.set_power(initial_pwr)
        else:
            servo_settle_time = round(time() - servo_start_time, 3)
            self.logger.warning(
                f"Servo did not converge within {self.max_iterations} iterations at {freq_ghz} GHz (Time: {servo_settle_time} s)")

        return servo_iterations, servo_settle_time