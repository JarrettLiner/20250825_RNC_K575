import logging
from src.instruments.bench import bench
from time import time

logger = logging.getLogger(__name__)

class VSG:
    def __init__(self):
        start_time = time()
        logger.info("Initializing VSG")
        self.vsg = bench().VSG_start()
        self.vsg.query('*RST; *OPC?')
        #  self.vsg.query('*OPC?')  # Ensure reset is complete
        # Common VSG settings
        self.vsg.query('SYSTem:RCL \'/var/user/Qorvo/NR5G_10MHz_UL_30kHzSCS_24QAM_24rb_0rbo_K575.savrcltxt\' ;*OPC?')
        #  self.vsg.write(':OUTPut1:AMODe AUTO')
        self.setup_time = time() - start_time
        logger.info(f"VSG initialized in {self.setup_time:.3f}s")

    def configure(self, freq, initial_power, vsg_offset):
        """
        Configure VSG for test:
          - Apply power offset
          - Set frequency
          - Set power level
          - Enable RF output

        Args:
            freq (float): Center frequency in Hz.
            initial_power (float): Initial power level in dBm.
            vsg_offset (float): Output power offset in dB.
        """
        # Apply output power offset
        self.vsg.write(f':SOUR1:POW:LEV:IMM:OFFS {vsg_offset:.3f}')
        self.vsg.query(':OUTput1:AMODe AUTO; *OPC?')  # Set ATTN mode to AUTO

        # Set RF frequency
        self.vsg.query(f':SOUR1:FREQ:CW {freq}; *OPC?')

        # Set output power
        self.vsg.query(f':SOUR1:POW:LEV:IMM:AMPL {initial_power}; *OPC?')

        # Enable RF output
        self.vsg.query(':OUTP1:STAT 1; *OPC?')

    def set_power(self, pwr):
        self.vsg.query(f':SOUR1:POW:LEV:IMM:AMPL {pwr}; *OPC?')
        #   self.vsg.query('*OPC?')

    def close(self):
        self.vsg.sock.close()