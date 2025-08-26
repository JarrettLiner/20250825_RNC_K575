from RsInstrument import RsInstrument
import time
import socket
import math

class NRX:
    """
    A Python class to control the R&S NRX Power Meter using SCPI commands via RsInstrument.

    This class provides methods to connect to the instrument, configure sensors and measurements,
    and perform power measurements such as average and burst power. Includes OPC synchronization
    for critical write commands to handle potential latency.
    """

    # List of commands requiring OPC synchronization due to state changes or processing time
    OPC_COMMANDS = [
        "*RST",
        "CALibration:ZERO:AUTO",
        "CONFIGURE:POWER",
        "INITiate:IMMediate",
        "SENSE:FREQuency",
        "CALCulate:FUNCtion",
        "CALCulate:RATio:PATHs"
    ]

    def __init__(self, resource_string="TCPIP::192.168.200.40::hislip0"):
        """
        Initialize the NRX class with a VISA resource string to connect to the instrument.

        :param resource_string: VISA resource string (default: 'TCPIP::192.168.200.80::hislip0')
        :raises RuntimeError: If connection fails with all attempted protocols
        """
        self.instr = None
        protocols = [
            resource_string,
            "TCPIP::192.168.200.40::inst0::INSTR",  # VXI-11
            "TCPIP::192.168.200.40::5025::SOCKET"   # Raw TCP/IP
        ]
        for protocol in protocols:
            try:
                print(f"Attempting connection with {protocol}")
                self.instr = RsInstrument(protocol, reset=False, options='VisaTimeout = 40000, SelectVisa = rs')
                self.instr.visa_timeout = 40000  # Set timeout to 40 seconds
                print(f"Connected to {protocol}")
                break
            except Exception as e:
                print(f"Failed to connect with {protocol}: {str(e)}")
        if self.instr is None:
            raise RuntimeError("Failed to connect to instrument with any protocol")

    def close(self):
        """
        Close the connection to the instrument and release resources.
        """
        if hasattr(self, 'instr') and self.instr:
            try:
                self.instr.close()
                print("Connection closed")
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    def opc_check(self, cmd):
        """
        Perform an OPC check after sending a command to ensure operation completion.

        :param cmd: SCPI command that was sent
        :return: True if OPC completes successfully, False otherwise
        """
        try:
            self.instr.write("*ESE 1")  # Enable Operation Complete bit
            self.instr.write("*SRE 32")  # Enable ESR bit in SRE
            self.instr.write(f"{cmd};*OPC")  # Send command with OPC
            while (self.instr.query_int("*ESR?") & 1) != 1:
                time.sleep(0.5)  # Poll every 0.5 seconds
            print(f"OPC check for '{cmd}' completed successfully")
            return True
        except Exception as e:
            print(f"Error in OPC check for '{cmd}': {str(e)}")
            error = self.get_error()
            print(f"Error queue after OPC check: {error}")
            return False

    def write(self, command):
        """
        Send an SCPI write command to the instrument, with OPC check for specified commands.

        :param command: SCPI command string to send
        :raises RuntimeError: If the command or OPC check fails
        """
        try:
            # Check if command requires OPC synchronization
            if any(opc_cmd in command for opc_cmd in self.OPC_COMMANDS):
                if not self.opc_check(command):
                    error = self.get_error()
                    raise RuntimeError(f"OPC synchronization failed for '{command}', Error queue: {error}")
                print(f"Sent command with OPC: {command}")
            else:
                self.instr.write(command)
                print(f"Sent command: {command}")
            time.sleep(0.2)  # Small delay for stability
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to write command '{command}': {str(e)}, Error queue: {error}")

    def query(self, command):
        """
        Send an SCPI query command to the instrument and return the response.

        :param command: SCPI query command string
        :return: Response from the instrument as a string
        :raises RuntimeError: If the query fails
        """
        try:
            # Use *WAI for measurement queries to ensure completion without OPC
            if "MEASURE" in command or "FETCH" in command:
                self.instr.write("*WAI")
            response = self.instr.query(command)
            print(f"Queried '{command}': {response}")
            return response
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to query '{command}': {str(e)}, Error queue: {error}")

    def identify(self):
        """
        Query the instrument's identification string.

        :return: Identification string (e.g., manufacturer, model, serial number, firmware version)
        """
        return self.query("*IDN?")

    def reset(self):
        """
        Reset the instrument to its default state.
        """
        self.write("*RST")
        print("Instrument reset complete.")

    def check_sensor_status(self, sensor):
        """
        Check if the specified sensor is connected and ready by attempting a safe query.

        :param sensor: Sensor number (1-4)
        :return: True if sensor is likely connected, False otherwise
        :raises ValueError: If sensor number is invalid
        """
        if not 1 <= sensor <= 4:
            raise ValueError("Sensor number must be between 1 and 4")
        try:
            self.query(f"SENSE{sensor}:TYPE?")
            return True
        except Exception as e:
            print(f"Error checking sensor {sensor} status: {str(e)}")
            error = self.get_error()
            print(f"Error queue after sensor check: {error}")
            return False

    def set_sensor_frequency(self, sensor, frequency):
        """
        Set the frequency for a specified sensor.

        :param sensor: Sensor number (1-4)
        :param frequency: Frequency value in Hz (e.g., 1e9 for 1 GHz)
        :raises ValueError: If sensor number or frequency is invalid
        """
        if not 1 <= sensor <= 4:
            raise ValueError("Sensor number must be between 1 and 4")
        if not 0 < frequency <= 110e9:  # Assuming max frequency of 110 GHz
            raise ValueError("Frequency must be between 0 Hz and 110 GHz")
        self.write(f"SENSE{sensor}:FREQuency {frequency}")

    def zero_sensor(self, sensor):
        """
        Perform a zeroing operation on the specified sensor.

        :param sensor: Sensor number (1-4)
        :raises ValueError: If sensor number is invalid
        :raises RuntimeError: If zeroing fails
        """
        if not 1 <= sensor <= 4:
            raise ValueError("Sensor number must be between 1 and 4")
        try:
            self.write(f"CALibration{sensor}:ZERO:AUTO ONCE")
            time.sleep(5)  # Increased delay for zeroing
            error = self.get_error()
            if "No error" not in error:
                raise RuntimeError(f"Zeroing sensor {sensor} failed: {error}")
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to zero sensor {sensor}: {str(e)}, Error queue: {error}")

    def measure_average_power(self, measurement):
        """
        Perform a scalar average power measurement for the specified measurement.

        :param measurement: Measurement number (1-4)
        :return: Measured average power value as a float (in dBm)
        :raises ValueError: If measurement number is invalid
        :raises RuntimeError: If measurement fails
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        try:
            self.write(f"CONFIGURE{measurement}:POWER:AVG")
            self.write(f"INITiate{measurement}:IMMediate")
            time.sleep(2)  # Increased delay for measurement stability
            response = self.query(f"MEASURE{measurement}:SCALar:POWER:AVG?")
            power_dbm = float(response)
            power_mw = 10 ** (power_dbm / 10)  # Convert dBm to mW
            if power_dbm < -70:  # Warn if power is very low
                print(f"Warning: Measured power ({power_dbm} dBm, {power_mw:.6f} mW) is very low. "
                      f"Check signal input on sensor {measurement} (e.g., 1 GHz, -20 dBm). "
                      f"Verify NRX front panel reading matches this value.")
            return power_dbm
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to measure average power: {str(e)}, Error queue: {error}")

    def measure_burst_power(self, measurement, aperture=None, resolution=None):
        """
        Perform a scalar burst average power measurement for the specified measurement.

        :param measurement: Measurement number (1-4)
        :param aperture: Optional aperture time in seconds (e.g., 0.001 for 1 ms)
        :param resolution: Optional resolution (e.g., in dB or linear units)
        :return: Measured burst power value as a float (in dBm)
        :raises ValueError: If measurement number or aperture is invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        cmd = f"MEASURE{measurement}:SCALar:POWER:BURSt:AVG"
        if aperture is not None:
            if not 0.0001 <= aperture <= 0.1:
                raise ValueError("Aperture must be between 0.1 ms and 100 ms")
            cmd += f" {aperture}"
            if resolution is not None:
                cmd += f",{resolution}"
        cmd += "?"
        try:
            self.write(f"CONFIGURE{measurement}:POWER:BURSt:AVG")
            self.write(f"INITiate{measurement}:IMMediate")
            time.sleep(2)
            response = self.query(cmd)
            power_dbm = float(response)
            power_mw = 10 ** (power_dbm / 10)  # Convert dBm to mW
            if power_dbm < -70:
                print(f"Warning: Measured power ({power_dbm} dBm, {power_mw:.6f} mW) is very low. "
                      f"Check signal input on sensor {measurement} (e.g., 1 GHz, -20 dBm). "
                      f"Verify NRX front panel reading matches this value.")
            return power_dbm
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to measure burst power: {str(e)}, Error queue: {error}")

    def configure_measurement(self, measurement, function):
        """
        Configure the measurement function for the specified measurement.

        :param measurement: Measurement number (1-4)
        :param function: Measurement function (e.g., 'POWER:AVG', 'POWER:BURSt:AVG')
        :raises ValueError: If measurement number or function is invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        valid_functions = ['POWER:AVG', 'POWER:BURSt:AVG', 'POWER:PEAK']
        if function not in valid_functions:
            raise ValueError(f"Function must be one of {valid_functions}")
        self.write(f"CONFIGURE{measurement}:{function}")

    def initiate_measurement(self, measurement):
        """
        Initiate a measurement on the specified measurement channel.

        :param measurement: Measurement number (1-4)
        :raises ValueError: If measurement number is invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        self.write(f"INITiate{measurement}:IMMediate")

    def fetch_scalar(self, measurement, function="POWER:AVG"):
        """
        Fetch the scalar result of a previously initiated measurement.

        :param measurement: Measurement number (1-4)
        :param function: Measurement function (default: 'POWER:AVG')
        :return: Measured value as a float (in dBm)
        :raises ValueError: If measurement number or function is invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        valid_functions = ['POWER:AVG', 'POWER:BURSt:AVG', 'POWER:PEAK']
        if function not in valid_functions:
            raise ValueError(f"Function must be one of {valid_functions}")
        try:
            response = self.query(f"FETCH{measurement}:SCALar:{function}?")
            return float(response)
        except Exception as e:
            error = self.get_error()
            raise RuntimeError(f"Failed to fetch scalar: {str(e)}, Error queue: {error}")

    def set_measurement_function(self, measurement, function):
        """
        Set the calculation function for the specified measurement.

        :param measurement: Measurement number (1-4)
        :param function: Calculation function (e.g., 'POWer')
        :raises ValueError: If measurement number or function is invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        valid_functions = ['POWer']  # Only POWer supported based on errors
        if function not in valid_functions:
            raise ValueError(f"Function must be one of {valid_functions}")
        self.write(f"CALCulate{measurement}:FUNCtion {function}")

    def set_ratio_sensors(self, measurement, sensor1, sensor2):
        """
        Set the sensors to be used for a ratio measurement.

        :param measurement: Measurement number (1-4)
        :param sensor1: First sensor number (1-4)
        :param sensor2: Second sensor number (1-4)
        :raises ValueError: If measurement or sensor numbers are invalid
        """
        if not 1 <= measurement <= 4:
            raise ValueError("Measurement number must be between 1 and 4")
        if not (1 <= sensor1 <= 4 and 1 <= sensor2 <= 4):
            raise ValueError("Sensor numbers must be between 1 and 4")
        self.write(f"CALCulate{measurement}:RATio:PATHs {sensor1},{sensor2}")

    def get_error(self):
        """
        Query the next error from the instrument's error queue.

        :return: Error message as a string (e.g., '+0,"No error"')
        """
        try:
            error = self.query("SYSTem:ERRor?")
            return error
        except Exception as e:
            return f"Error querying error queue: {str(e)}"

    @staticmethod
    def test_network(ip_address="192.168.200.40", port=4880):
        """
        Test network connectivity to the instrument's IP address.

        :param ip_address: IP address to test (default: '192.168.200.80')
        :param port: Port to test (default: 4880 for HiSLIP, 111 for VXI-11, 5025 for TCP/IP)
        :return: True if connection is successful, False otherwise
        """
        try:
            with socket.create_connection((ip_address, port), timeout=5) as sock:
                print(f"Network test: Successfully connected to {ip_address}:{port}")
                return True
        except Exception as e:
            print(f"Network test: Failed to connect to {ip_address}:{port}: {str(e)}")
            return False

if __name__ == "__main__":
    nrx = None  # Initialize nrx to None to avoid NameError
    try:
        # Test network connectivity for multiple protocols
        print("Testing network connectivity...")
        NRX.test_network(ip_address="192.168.200.40", port=4880)  # HiSLIP
        NRX.test_network(ip_address="192.168.200.40", port=111)   # VXI-11
        NRX.test_network(ip_address="192.168.200.40", port=5025)  # Raw TCP/IP

        # Create an instance of the NRX class
        print("Connecting to NRX...")
        nrx = NRX("TCPIP::192.168.200.80::hislip0")

        # Verify the connection by querying the instrument's identity
        print("Querying instrument ID...")
        print("Instrument ID:", nrx.identify())

        # Check sensor status
        print("Checking sensor 1 status...")
        sensor1_connected = nrx.check_sensor_status(1)
        print("Sensor 1 status:", "Connected" if sensor1_connected else "Not connected")

        # Reset the instrument
        print("Resetting instrument...")
        nrx.reset()

        # Configure sensor 1
        print("Setting sensor 1 frequency to 1 GHz...")
        nrx.set_sensor_frequency(1, 1e9)
        # Zeroing commented out due to error with signal applied
        # print("Zeroing sensor 1...")
        # try:
        #     nrx.zero_sensor(1)
        #     print("Sensor 1 zeroed successfully.")
        # except RuntimeError as e:
        #     print(f"Warning: {str(e)}. Proceeding with measurement anyway.")
        print("Note: Zeroing skipped. Ensure no signal is applied for zeroing, or proceed if accuracy is sufficient.")

        # Measure average power for sensor 1
        print("Measuring average power for sensor 1...")
        print("Note: Ensure a signal is applied (e.g., 1 GHz, -20 dBm) for accurate measurements.")
        try:
            power1_dbm = nrx.measure_average_power(1)
            power1_mw = 10 ** (power1_dbm / 10)
            print(f"Average power (sensor 1): {power1_dbm} dBm ({power1_mw:.6f} mW)")
        except RuntimeError as e:
            print(f"Sensor 1 measurement failed: {str(e)}")
            power1_dbm = None

        # Check sensor 2 status
        print("Checking sensor 2 status...")
        sensor2_connected = nrx.check_sensor_status(2)
        print("Sensor 2 status:", "Connected" if sensor2_connected else "Not connected")

        # Configure and measure sensor 2 if connected
        if sensor2_connected:
            print("Setting sensor 2 frequency to 1 GHz...")
            nrx.set_sensor_frequency(2, 1e9)
            # Zeroing commented out due to error with signal applied
            # print("Zeroing sensor 2...")
            # try:
            #     nrx.zero_sensor(2)
            #     print("Sensor 2 zeroed successfully.")
            # except RuntimeError as e:
            #     print(f"Warning: {str(e)}. Proceeding with measurement anyway.")
            print("Note: Zeroing skipped. Ensure no signal is applied for zeroing, or proceed if accuracy is sufficient.")
            print("Measuring average power for sensor 2...")
            try:
                power2_dbm = nrx.measure_average_power(2)
                power2_mw = 10 ** (power2_dbm / 10)
                print(f"Average power (sensor 2): {power2_dbm} dBm ({power2_mw:.6f} mW)")
                # Calculate power difference
                if power1_dbm is not None:
                    difference_dbm = power1_dbm - power2_dbm
                    print(f"Power difference (sensor 1 - sensor 2): {difference_dbm:.6f} dBm")
                    # Calculate power ratio (sensor 1 / sensor 2)
                    ratio_db = 10 * math.log10(power1_mw / power2_mw)
                    print(f"Power ratio (sensor 1 / sensor 2): {ratio_db:.6f} dB")
            except RuntimeError as e:
                print(f"Sensor 2 measurement or calculations failed: {str(e)}")
        else:
            print("Sensor 2 not connected, skipping sensor 2 measurement and calculations")

        '''
        # Suggest checking supported CALC:FUNC commands
        print("Checking supported CALCulate:FUNCtion...")
        try:
            calc_func = nrx.query("CALCulate1:FUNCtion?")
            print(f"Current CALCulate:FUNCtion: {calc_func}")
        except Exception as e:
            print(f"Failed to query CALCulate:FUNCtion: {str(e)}. Consult NRX manual for supported functions.")
        '''
        # Check for errors
        print("Checking error queue...")
        print("Error queue:", nrx.get_error())

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Close the connection if nrx was created
        if nrx is not None:
            nrx.close()