import logging
from time import time
from src.instruments.bench import bench

logger = logging.getLogger(__name__)

class PowerMeter:
    def __init__(self, host="192.168.200.40", port=5025):
        self.bench = bench()
        start_time = time()
        try:
            self.instr = self.bench.NRX_start()  # Get iSocket instance
            #  self.instr.query('*RST; *OPC?')
            #  self.instr.write(':INITiate1:ALL:IMMediate')
            #  self.instr.query('*OPC?')
            self.setup_time = time() - start_time
            logger.info(f"PowerMeter (NRX) initialized in {self.setup_time:.3f}s")
        except Exception as e:
            logger.error(f"PowerMeter initialization failed: {str(e)}")
            raise

    def configure(self, freq, input_offset, output_offset):
        try:
            #  self.instr.query(':INITiate1:ALL:IMMediate; *OPC?')
            self.instr.write(f':SENS1:FREQ {freq}')
            self.instr.write(f':SENS2:FREQ {freq}')
            self.instr.write(f'CALCulate1:CHANnel1:CORRection:OFFSet:MAGNitude {input_offset}')
            self.instr.write(f'CALCulate1:CHANnel1:CORRection:OFFSet:STATe ON')
            self.instr.write(f'CALCulate2:CHANnel1:CORRection:OFFSet:MAGNitude {output_offset}')
            self.instr.write(f'CALCulate2:CHANnel1:CORRection:OFFSet:STATe ON')
            #  self.instr.write(':INITiate1:ALL:IMMediate')
            #  self.instr.query('*OPC?')
        except Exception as e:
            logger.error(f"PowerMeter configuration failed: {str(e)}")
            raise

    def measure(self):
        try:
            #  self.instr.query(':INITiate1:ALL:IMMediate;*OPC?')  # Ensure this command is sent before every reading
            input_power = self.instr.queryFloat(':MEAS1?')
            #  self.instr.write(':INITiate1:ALL:IMMediate')  # Added before second reading
            output_power = self.instr.queryFloat(':MEAS2?')
            return input_power, output_power
        except Exception as e:
            logger.error(f"Power measurement failed: {str(e)}")
            raise

    def write_command_opc(self, command: str) -> None:
        try:
            self.instr.write('*ESE 1')  # Enable Operation Complete bit
            self.instr.write('*SRE 32')  # Enable service request for OPC
            self.instr.write(f'{command};*OPC')  # Send command with OPC
            while (int(self.instr.query('*ESR?')) & 1) != 1:
                time.sleep(0.2)  # Wait briefly between polls
            logger.info(f"Command '{command}' completed with OPC synchronization.")
        except Exception as e:
            logger.error(f"Error during OPC write for command '{command}': {str(e)}")
            raise

    def close(self):
        try:
            self.instr.sock.close()
            logger.info("PowerMeter socket closed")
        except Exception as e:
            logger.error(f"PowerMeter close failed: {str(e)}")
            raise