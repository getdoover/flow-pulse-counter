import logging
from typing import TYPE_CHECKING
import asyncio
import math
import time
from typing import Callable

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
        pulse_edge_mode: str,    
        init_estimate: int = None,
        max_rpm: int = None,
        flow_rate_sensitivity: float = 0.1,
        measurement_variance: float = 50,
        set_tags=None,
        debug_mode: bool = False,
    ):
        self.plt_iface = plt_iface
        self._l_per_pulse = l_per_pulse
        self.volume_unit_litres = volume_unit_litres
        self.time_unit_seconds = time_unit_seconds
        self.pulse_pin = pulse_pin
        
        self.pulse_edge_mode = pulse_edge_mode
        self.set_tags=set_tags

        self.pulse_count = 0
        self._is_pumping = False
        self.should_ignore_next_pulse = False
        self.total_count = 0
        self._last_given_pulse_count = 0

        self.target_flow_rate = 2.5  # l/hr
        self.current_duty_cycle = 0.5
        # self.measurement_variance = self.calc_measurement_variance(
        #     self.current_duty_cycle
        # )
        # self.max_rpm = max_rpm
        self.measurement_variance = measurement_variance
                
        self.sleep_time = 0.2
        self.decay_start_time = None
        self.debug_mode = debug_mode

        self.reset_kalman(sensitivity=flow_rate_sensitivity, init_estimate=init_estimate)

        self.pulse_counter = self.plt_iface.get_new_pulse_counter(
            di=self.pulse_pin,
            edge=self.pulse_edge_mode,
            callback=self.pulse_counter_callback,
            rate_window_secs=60,
        )
        log.info(f"Flow meter initialized with pulse edge mode: {self.pulse_edge_mode}")
        
    @staticmethod
    def smooth_decay_99_at_dt(t: float, flow_rate_dt: float, last_flow_rate: float = 1.0) -> float:
        """
        Smooth (C∞) monotone decay:
        f(0)                = last_flow_rate
        f(1.2*flow_rate_dt) = 0.99*last_flow_rate
        f(2.5*flow_rate_dt) = 0.50*last_flow_rate
        f(4.0*flow_rate_dt) = 0.01*last_flow_rate
        """
        if flow_rate_dt <= 0:
            raise ValueError("flow_rate_dt must be positive")
        x = t / flow_rate_dt
        a = 3.59523983369514
        b = 2.41449238931183
        c = 0.807435919156309
        # Equivalent: last_flow_rate * ((1 + e^{a(x-b)}) / (1 + e^{-ab}))^{-c}
        return last_flow_rate * (1 + math.exp(-a*b))**c / (1 + math.exp(a*(x - b)))**c

    def set_decay_flow_rate_func(self, flow_rate: float):
        self.decay_start_time = time.monotonic()
        flow_rate_dt = 1/((flow_rate / self.l_per_pulse) / self.time_unit_seconds)
        self.decay_func = lambda t: self.smooth_decay_99_at_dt(t, flow_rate_dt, flow_rate)
        
    async def setup(self):
        print(" ----- flow_meter setup")
        self.main_loop_task = asyncio.create_task(self.main_loop())
        
    async def main_loop(self):
        while True:
            if self.decay_start_time is not None:
                dt = time.monotonic() - self.decay_start_time
                flow_rate = self.decay_func(dt)
                if flow_rate < 0.001:
                    self.decay_start_time = None
                    flow_rate = 0
            else:
                flow_rate = 0
                dt = 0  # Set dt to 0 when not in decay mode
            self.record_measurement(flow_rate, dt=dt)
            
            if self.debug_mode:
                tags = {
                    "kf-flow-rate": self.flow_rate,
                    "raw-flow-rate": flow_rate,
                    "decay-start-time": self.decay_start_time,
                    "dt": dt,
                }
                await self.set_tags(tags=tags)
            await asyncio.sleep(self.sleep_time)

    @property
    def l_per_pulse(self):
        return self._l_per_pulse

    ## The kalman filter is measuring inter pulse time, so the flow rate is in l/hr
    def reset_kalman(
        self, sensitivity: float = 0.1, init_estimate: int = 0, init_error_estimate: float = 0.001,
    ):
        ## Set the kalman filter initial estimate to the target flow rate with a tight error estimate
        self.kf = KalmanFilter1D(
            process_variance=sensitivity,
            initial_estimate=init_estimate,
            initial_error_estimate=init_error_estimate,
        )

    def record_measurement(self, measurement, dt=None):
        if dt is None:
            dt=measurement
        self.kf.update(measurement, self.measurement_variance, dt=dt)

    def pulse_counter_callback(self, di, di_value, dt_secs, counter, edge):
        if self.should_ignore_next_pulse:
            self.should_ignore_next_pulse = False
            return
        ## Get the dt in seconds of the pulse, coerced between 0.01 and 120 secs
        dt_secs = max(0.01, min(dt_secs, 120))
        self.last_dt = dt_secs
        
        raw_flow_rate = self.dt_to_flow_rate(dt_secs)
        self.set_decay_flow_rate_func(raw_flow_rate)
        # print("\n ***** \n     dt_secs: ", dt_secs, " \n ***** \n")
        # self.record_measurement(dt_secs)
        self.pulse_count += 1
        self.total_count += 1
        self.last_pulse_time = time.monotonic()
        log.info(f"incrementing total count: {self.total_count}, dt_secs: {dt_secs}")

    def dt_to_flow_rate(self, dt_secs: float) -> float:
        return (1 / dt_secs) * self.l_per_pulse * self.time_unit_seconds
    
    def get_total_pulses(self, last_recorded):
        """
        Get the total pulses recorded since the last call.
        """
        new_pulses = self.total_count - self._last_given_pulse_count
        new_total = last_recorded + new_pulses
        self._last_given_pulse_count = self.total_count
        return new_total
    
    @property
    def flow_rate(self):
        return self.kf.estimate
    
    # def calc_measurement_variance(self, duty_cycle):
    #     # limit duty cycle to 0 - 100
    #     duty_cycle = min(1, max(0, duty_cycle)) * 100
    #     log.debug(f"Duty Cycle: {duty_cycle}")
    #     # approximate variance of pulse measurements
    #     try:
    #         mv = (1.15 * (1 / ((10 ** (-2.7)) * (duty_cycle**1.3)))) - 1.2
    #     except ZeroDivisionError:
    #         mv = 2

    #     log.debug(f"measurement variance: {mv}")
    #     return mv
    
    # @property
    # def is_pumping(self):
    #     return self._is_pumping

    # @is_pumping.setter
    # def is_pumping(self, value):
    #     # Reset the kalman if the pump has been restarted
    #     if self.is_pumping is False and value is True:
    #         self.reset_kalman(sensitivity=1, init_estimate=0, init_error_estimate=0.1)
    #         self.should_ignore_next_pulse = True
            
    #     if value is False:
    #         self.pulse_count = 0
            
    #     self._is_pumping = value

    # def get_estimated_inter_pulse_time(self):
    #     ## Calculate from the target flow rate
    #     target_pulse_rate = self.target_flow_rate / self.l_per_pulse
        
    #     if self.max_rpm is not None and self.max_rpm > 0:
    #         if target_pulse_rate > self.max_rpm / 60 * self.time_unit_seconds:
    #             target_pulse_rate = self.max_rpm / 60 * self.time_unit_seconds
    #     try:
    #         return self.time_unit_seconds / target_pulse_rate
    #     except ZeroDivisionError:
    #         return 0

    # def set_target_flow_rate(self, target_flow_rate):
    #     if target_flow_rate == self.target_flow_rate and self.is_pumping:
    #         log.debug("Target flow rate matches target flow rate. Skipping...")
    #         return
    #     if target_flow_rate == 0:
    #         self.is_pumping = False
    #         return
    #     elif target_flow_rate > 0:
    #         self.is_pumping = True

    #     ## If the target flow rate has changed, reset the kalman filter
    #     log.info(f"Flow meter setting target flow rate: {target_flow_rate}")
    #     self.target_flow_rate = target_flow_rate
    #     self.reset_kalman()
    #     # self.measurement_variance = self.calc_measurement_variance(
    #     #     self.current_duty_cycle
    #     # )

    # def set_current_duty_cycle(self, current_duty_cycle):
    #     self.current_duty_cycle = current_duty_cycle
    #     self.measurement_variance = self.calc_measurement_variance(current_duty_cycle)
