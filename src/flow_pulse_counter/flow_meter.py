import logging
from typing import TYPE_CHECKING

from pydoover.utils.kalman import KalmanFilter1D

if TYPE_CHECKING:
    from pydoover.docker import PlatformInterface
    from .app_config import SIAInjectionControllerConfig

log = logging.getLogger()


class FlowMeter:
    def __init__(
        self,
        plt_iface: "PlatformInterface",
        l_per_pulse: float,
        volume_unit_litres: float,
        time_unit_seconds: int,
        pulse_pin: int,        
        max_rpm: int = None,
    ):
        self.plt_iface = plt_iface
        self._l_per_pulse = l_per_pulse
        self.volume_unit_litres = volume_unit_litres
        self.time_unit_seconds = time_unit_seconds
        self.pulse_pin = pulse_pin
        self.max_rpm = max_rpm

        self.pulse_count = 0
        self._is_pumping = False
        self.should_ignore_next_pulse = False
        self.total_count = 0
        self._last_given_pulse_count = 0

        self.target_flow_rate = 2.5  # l/hr
        self.current_duty_cycle = 0.5
        self.measurement_variance = self.calc_measurement_variance(
            self.current_duty_cycle
        )

        self.reset_kalman()

        self.pulse_counter = self.plt_iface.get_new_pulse_counter(
            di=self.config.flow_pulse_pin.value,
            edge="rising",
            callback=self.pulse_counter_callback,
            rate_window_secs=60,
        )

    @property
    def l_per_pulse(self):
        return self._l_per_pulse

    ## The kalman filter is measuring inter pulse time, so the flow rate is in l/hr
    def reset_kalman(
        self, sensitivity: float = 0.0001, init_estimate: int = None, init_error_estimate: float = 0.001,
    ):
        ## Set the kalman filter initial estimate to the target flow rate with a tight error estimate
        self.kf = KalmanFilter1D(
            process_variance=sensitivity,
            initial_estimate=init_estimate or self.get_estimated_inter_pulse_time(),
            initial_error_estimate=init_error_estimate,
        )

    def record_measurement(self, measurement):
        self.kf.update(measurement, self.measurement_variance, dt=measurement)

    def get_inter_pulse_time(self):
        return self.kf.estimate

    def calc_measurement_variance(self, duty_cycle):
        # limit duty cycle to 0 - 100
        duty_cycle = min(1, max(0, duty_cycle)) * 100
        log.debug(f"Duty Cycle: {duty_cycle}")
        # approximate variance of pulse measurements
        try:
            mv = (1.15 * (1 / ((10 ** (-2.7)) * (duty_cycle**1.3)))) - 1.2
        except ZeroDivisionError:
            mv = 2

        log.debug(f"measurement variance: {mv}")
        return mv

    def pulse_counter_callback(self, di, di_value, dt_secs, counter, edge):
        if self.should_ignore_next_pulse:
            self.should_ignore_next_pulse = False
            return

        ## Get the dt in seconds of the pulse, coerced between 0.01 and 120 secs
        dt_secs = max(0.01, min(dt_secs, 120))
        # print("\n ***** \n     dt_secs: ", dt_secs, " \n ***** \n")
        self.record_measurement(dt_secs)
        self.pulse_count += 1
        self.total_count += 1

    def get_total_pulses(self, last_recorded):
        """
        Get the total pulses recorded since the last call.
        """
        new_pulses = self.total_count - self._last_given_pulse_count
        new_total = last_recorded + new_pulses
        self._last_given_pulse_count = self.total_count
        return new_total
    
    @property
    def is_pumping(self):
        return self._is_pumping

    @is_pumping.setter
    def is_pumping(self, value):
        # Reset the kalman if the pump has been restarted
        if self.is_pumping is False and value is True:
            self.reset_kalman()
            self.should_ignore_next_pulse = True
            
        if value is False:
            self.pulse_count = 0
            
        self._is_pumping = value

    def get_estimated_inter_pulse_time(self):
        ## Calculate from the target flow rate
        target_pulse_rate = self.target_flow_rate / self.l_per_pulse
        
        if self.max_rpm is not None and self.max_rpm > 0:
            if target_pulse_rate > self.max_rpm / 60 * self.time_unit_seconds:
                target_pulse_rate = self.max_rpm / 60 * self.time_unit_seconds
        try:
            return self.time_unit_seconds / target_pulse_rate
        except ZeroDivisionError:
            return 0

    @property
    def flow_rate(self):
        if not self.is_pumping:
            # print("Flow rate is 0 (not pumping)")
            return 0

        return (self.time_unit_seconds / self.kf.estimate) * self.l_per_pulse

    def set_target_flow_rate(self, target_flow_rate):
        if target_flow_rate == self.target_flow_rate and self.is_pumping:
            log.debug("Target flow rate matches target flow rate. Skipping...")
            return
        if target_flow_rate == 0:
            self.is_pumping = False
            return
        elif target_flow_rate > 0:
            self.is_pumping = True

        ## If the target flow rate has changed, reset the kalman filter
        log.info(f"Flow meter setting target flow rate: {target_flow_rate}")
        self.target_flow_rate = target_flow_rate
        self.reset_kalman()
        # self.measurement_variance = self.calc_measurement_variance(
        #     self.current_duty_cycle
        # )

    def set_current_duty_cycle(self, current_duty_cycle):
        self.current_duty_cycle = current_duty_cycle
        self.measurement_variance = self.calc_measurement_variance(current_duty_cycle)
