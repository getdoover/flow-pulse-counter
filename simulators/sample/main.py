import random
import time

from pydoover.docker import Application, run_app
from pydoover.config import Schema


class FlowPulseSimulator(Application):
    """Simulates a flow meter by toggling a digital output to generate pulses.

    Cycles through different flow rate scenarios:
    - Idle (no flow): 10s
    - Low flow (~2 L/min at 450 pulses/L = ~15 Hz): 20s
    - Normal flow (~10 L/min at 450 pulses/L = ~75 Hz): 30s
    - High flow (~25 L/min at 450 pulses/L = ~187 Hz): 15s
    """

    loop_target_period = 0.05  # 50ms for fast pulse generation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pin_state = False
        self.cycle_start = 0
        self.pulse_interval = 0  # seconds between pulses (0 = no pulses)
        self.last_pulse_time = 0

    async def setup(self):
        self.cycle_start = time.time()
        self.last_pulse_time = time.time()

    async def main_loop(self):
        now = time.time()
        elapsed = now - self.cycle_start

        # Cycle through flow scenarios
        if elapsed < 10:
            # Idle - no flow
            self.pulse_interval = 0
        elif elapsed < 30:
            # Low flow (~2 L/min)
            self.pulse_interval = 1.0 / 15.0
        elif elapsed < 60:
            # Normal flow (~10 L/min)
            self.pulse_interval = 1.0 / 75.0
        elif elapsed < 75:
            # High flow (~25 L/min)
            self.pulse_interval = 1.0 / 187.0
        else:
            # Reset cycle
            self.cycle_start = now
            self.pulse_interval = 0

        # Generate pulses by toggling digital output
        if self.pulse_interval > 0:
            if now - self.last_pulse_time >= self.pulse_interval:
                self.pin_state = not self.pin_state
                await self.platform_iface.set_do_async(pin=1, value=self.pin_state)
                self.last_pulse_time = now
        else:
            if self.pin_state:
                self.pin_state = False
                await self.platform_iface.set_do_async(pin=1, value=False)


def main():
    """Run the flow pulse simulator."""
    run_app(FlowPulseSimulator(config=Schema()))


if __name__ == "__main__":
    main()
