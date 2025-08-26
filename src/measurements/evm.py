import logging
from multiprocessing.synchronize import SEM_VALUE_MAX
from time import time
from src.measurements.vsa import VSA
from src.instruments.bench import bench

logger = logging.getLogger(__name__)

class EVM:
    def __init__(self, vsa):
        self.vsa = vsa

    def measure(self, freq_str, vsa_offset):
        start_time = time()  # Corrected to time()
        self.vsa.set_to_evm_mode()
        self.vsa.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV:OFFS {vsa_offset:.2f}')
        vsa_power = self.vsa.queryFloat('FETCh:CC1:SUMMary:POWer:AVERage?')
        evm = self.vsa.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
        self.vsa.write('CONF:GEN:CONT:STAT OFF')
        measure_time = time() - start_time
        return vsa_power, evm, measure_time

    def get_evm(self):
        try:
            evm = self.vsa.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
            return evm
        except Exception as e:
            logger.error(f"Failed to get EVM: {str(e)}")
            raise