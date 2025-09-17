import logging
from time import time
from time import sleep
from src.instruments.bench import bench

logger = logging.getLogger(__name__)

class PowerMeter:
    def __init__(self, host="192.168.200.40", port=5025):
        self.bench = bench()
        start_time = time()
        try:
            self.instr = self.bench.NRX_start()  # Get iSocket instance
            #  self.instr.query('*OPC?')
            #  self.instr.write(':INITiate:ALL:CONTinuous ON')
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
            #  self.instr.write(':INIT1; *WAI')
            #  self.instr.write(':INIT2; *WAI')
            #  self.instr.write(':INITiate:ALL:CONTinuous ON')
            #  self.instr.write(':INITiate1:ALL:IMMediate')
            #  self.instr.query('*OPC?')
        except Exception as e:
            logger.error(f"PowerMeter configuration failed: {str(e)}")
            raise

    def measure(self):
        try:
            meas_start_time = time()
            #  self.instr.query(':INITiate1:ALL:IMMediate;*OPC?')  # Ensure this command is sent before every reading
            #  self.instr.write(':INIT1:CONT')
            #  self.instr.write(':INIT2:CONT')
            #  sleep(0.01)
            #  self.instr.write('*TRG')  # Trigger measurement
            self.instr.write('INIT1:IMM')  # Start measurement on channel 1
            input_power = self.instr.queryFloat('FETC1?')
            #  input_power = self.instr.queryFloat('MEAS1?')
            #  self.instr.query('*OPC?')
            #  self.instr.write(':INITiate1:ALL:IMMediate')  # Added before second reading
            self.instr.write('INIT2:IMM')  # Start measurement on channel 1
            output_power = self.instr.queryFloat('FETC2? ')
            #  output_power = self.instr.queryFloat('MEAS2?')
            #  self.instr.query('*OPC?')
            measurement_time = time() - meas_start_time
            print(f"PowerMeter (NRX) measured in {measurement_time:.3f}s")
            print(f"Input Power: {input_power} dBm, Output Power: {output_power} dBm")
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
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pm = PowerMeter()
    pm.configure(3.5e9, -1.0, -1.0)
    input_pwr, output_pwr = pm.measure()
    print(f"Input Power: {input_pwr} dBm, Output Power: {output_pwr} dBm")
    pm.measure()
    pm.close()