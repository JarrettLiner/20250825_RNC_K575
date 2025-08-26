import logging
from time import time
from src.measurements.vsa import VSA
from src.instruments.bench import bench

logger = logging.getLogger(__name__)

class K575_EVM:
    def __init__(self, vsa):
        self.vsa = vsa

    def measure(self, freq_str, vsa_offset, K575_iter):
        start_time = time()
        self.vsa.instr.query(f':SENS:FREQ:CENT {freq_str}; *OPC?')
        self.vsa.instr.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV:OFFS {vsa_offset:.2f}')
        self.vsa.instr.query('INST:SEL "5GNR"; *OPC?')
        self.vsa.instr.query('CONF:GEN:CONN:STAT ON; *OPC?')
        self.vsa.instr.query('CONF:GEN:CONT:STAT ON; *OPC?')
        self.vsa.instr.query('CONF:GEN:RFO:STAT ON; *OPC?')
        self.vsa.instr.query('CONF:SETT:RF; *OPC?')
        self.vsa.instr.query('CONF:SETT:NR5G; *OPC?')
        self.vsa.instr.query('INIT:CONT OFF; *OPC?')
        self.vsa.instr.query('INIT:IMM; *OPC?')
        evm = self.vsa.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
        self.vsa.instr.query(f'SENS:ADJ:NCAN:AVER:COUN {K575_iter}; *OPC?')
        self.vsa.instr.query('SENS:ADJ:NCAN:AVER:STST ON; *OPC?')
        self.vsa.instr.query('INIT:IMM; *OPC?')
        K575_evm = self.vsa.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
        measure_time = time() - start_time
        logger.info(f"EVM: {evm} K575 EVM: {K575_evm} with {K575_iter} Averages")
        return K575_evm, measure_time