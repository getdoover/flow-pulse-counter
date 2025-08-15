import asyncio
import logging
import os

import aiohttp

from pydoover.docker import Application, run_app
from pydoover.config import Schema

log = logging.getLogger()


class PlatformInterfaceSim:
    def __init__(self, endpoint: str = "http://localhost:8080"):
        self.endpoint = endpoint
        self.session = aiohttp.ClientSession()

    async def request(self, method, path, data: dict):
        return await self.session.request(method, self.endpoint + path, json=data)

    async def set_di(self, di, enabled: bool):
        await self.request("POST", f"/di/{di}", {"value": enabled})


class FlowMeterSimulator(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.platform_sim: PlatformInterfaceSim = None
        self.pulse_pin = int(os.environ.get("PULSE_PIN", 0))

        self.pulse_interval: float = 0.0
        self.last_intensity: float = 0.0

        self.pulse_task = None

    async def setup(self):
        log.info("Setting up Flow Meter Pulse Simulator")
        self.platform_sim = PlatformInterfaceSim()
        self.update_pulse_interval(1)

    async def main_loop(self):
        freq = float(self.get_tag("sim_pulse_rate_hz"))
        if freq != self.last_freq:
            log.info(f"Flow rate changed to {freq}, updating pulse interval.")
            self.update_pulse_interval(freq)
            self.last_freq = freq

    def update_pulse_interval(self, freq):
        log.info(f"Updating pulse interval for freq: {freq}")
        try:
            self.pulse_interval = 1/freq
        except Exception as e:
            log.error(f"Error updating pulse interval: {e}")
            self.pulse_interval = 1

        if self.pulse_task:
            self.pulse_task.cancel()
        self.pulse_task = asyncio.create_task(self.do_pulses())

    async def do_pulses(self):
        log.info(f"Starting pulse task with interval: {self.pulse_interval} seconds")
        await self.platform_sim.set_di(self.pulse_pin, True)
        log.info("Pulse pin set to HIGH, waiting for interval to elapse.")
        while True:
            log.info(f"Waiting {self.pulse_interval} seconds before next pulse")
            await asyncio.sleep(self.pulse_interval)

            log.info("Sending pulse")
            await self.platform_sim.set_di(self.pulse_pin, False)
            await asyncio.sleep(0.1)
            await self.platform_sim.set_di(self.pulse_pin, True)



def main():
    """Run the sample simulator application."""
    c = Schema()
    setattr(c, "_Schema__element_map", {})
    run_app(FlowMeterSimulator(config=c))

if __name__ == "__main__":
    main()
