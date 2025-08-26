import logging
from time import time
from src.instruments.bench import bench
from src.measurements.power_meter import PowerMeter

logger = logging.getLogger(__name__)

class VSA:
    def __init__(self, host="192.168.200.20", port=5025):
        self.bench = bench()
        start_time = time()
        try:
            self.instr = self.bench.VSA_start()  # Get iSocket instance
            self.instr.write('*RST')
            self.instr.query('*OPC?')
            self.instr.query('MMEM:SEL:ITEM:HWS ON; *OPC?')
            self.instr.query(r'MMEM:LOAD:STAT 1,"C:\R_S\instr\user\Qorvo\5GNR_UL_10MHz_256QAM_30kHz_24RB_0RBO"; *OPC?')
            self.instr.query(':SENS:ADJ:LEV; *OPC?')
            self.instr.query(':SENS:ADJ:EVM; *OPC?')
            '''
            self.instr.query('INST:COUP:CENT ALL; *OPC?')
            self.instr.query('INST:COUP:RLEV ALL; *OPC?')
            self.instr.query('INST:COUP:ATT ALL; *OPC?')
            self.instr.query('INST:COUP:USER1:STAT ON; *OPC?')
            self.instr.query('INST:SEL "5GNR"; *OPC?')
            self.instr.query('INIT:CONT OFF; *OPC?')
            '''
            self.instr.query('CONF:GEN:CONN:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:CONT:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:RFO:STAT ON; *OPC?')
            self.instr.query('CONF:SETT:RF; *OPC?')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            '''
            self.instr.query(':TRIG:SEQ:SOUR EXT; *OPC?')
            '''
            self.instr.query('INIT:IMM; *OPC?')
            self.setup_time = time() - start_time
            logger.info(f"VSA initialized in {self.setup_time:.3f}s")
        except Exception as e:
            logger.error(f"VSA initialization failed: {str(e)}")
            raise

    def autolevel(self):
        self.instr.query(':SENS:ADJ:LEV; *OPC?')

    def autoEVM(self):
        self.instr.query(':SENS:ADJ:EVM; *OPC?')

    def set_ref_level(self, ref_level):
        try:
            self.instr.query(f'DISP:WIND:TRAC:Y:SCAL:RLEV {ref_level:.2f}; *OPC?')
            logger.info(f"VSA reference level set to {ref_level:.2f} dBm")
        except Exception as e:
            logger.error(f"Setting VSA reference level failed: {str(e)}")
            raise

    def configure(self, freq, vsa_offset):
        try:
            '''
            self.instr.query(f':SENS:FREQ:CENT {freq}; *OPC?')
            self.instr.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV:OFFS {vsa_offset:.2f}')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            self.instr.query(':INIT:IMM; *OPC?')
            '''
        except Exception as e:
            logger.error(f"VSA configuration failed: {str(e)}")
            raise

    def queryFloat(self, command):
        try:
            return float(self.instr.query(command))
        except ValueError:
            logger.warning(f"Non-float response for {command}")
            return float('nan')

    def measure_evm(self, freq_str, vsa_offset, ref_lev):
        try:

            self.instr.query(f':SENS:FREQ:CENT {freq_str}; *OPC?')
            self.instr.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV:OFFS {vsa_offset:.2f}')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            self.instr.query(':SENS:ADJ:LEV; *OPC?')
            self.instr.query(':SENS:ADJ:EVM; *OPC?')
            self.instr.query(':DISP:WIND3:SUBW1:TRAC:Y:SCAL:AUTO ALL; *OPC?')
            start_time = time()
            '''
            self.instr.query('INST:SEL "5GNR"; *OPC?')
            self.instr.query('CONF:GEN:CONN:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:CONT:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:RFO:STAT ON; *OPC?')
            self.instr.query('CONF:SETT:RF; *OPC?')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            '''
            #  self.instr.write('INIT:CONT OFF; *OPC?')
            self.instr.write('INIT:IMM; *WAI')
            vsa_power = self.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:POW:AVERage?')
            evm = self.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
            evm_measure_time = time() - start_time
            logger.info(f"EVM measurement: Power={vsa_power}, EVM={evm}, Time={evm_measure_time}")
            start_time = time()
            self.instr.write('CONF:NR5G:MEAS ACLR')
            self.instr.write('INIT:IMM;*WAI')
            aclr_list = self.instr.query('CALC:MARK:FUNC:POW:RES? ACP')
            chan_pow = float(aclr_list.split(',')[0])
            adj_chan_lower = float(aclr_list.split(',')[1])
            adj_chan_upper = float(aclr_list.split(',')[2])
            aclr_measure_time = time() - start_time
            self.instr.write('CONF:NR5G:MEAS EVM')
            logger.info(f"ACLR measurement: Channel Power={chan_pow}, Lower Adjacent={adj_chan_lower}, Upper Adjacent={adj_chan_upper}, Time={aclr_measure_time}")
            return vsa_power, evm, evm_measure_time, chan_pow, adj_chan_lower, adj_chan_upper, aclr_measure_time
        except Exception as e:
            logger.error(f"EVM measurement failed: {str(e)}")
            raise

    def measure_K575_evm(self, freq_str, vsa_offset, avg):
        try:
            start_time = time()
            '''
            self.instr.query(f':SENS:FREQ:CENT {freq_str}; *OPC?')
            self.instr.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV:OFFS {vsa_offset:.2f}')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            
            self.instr.query('INST:SEL "5GNR"; *OPC?')
            self.instr.query('CONF:GEN:CONN:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:CONT:STAT ON; *OPC?')
            self.instr.query('CONF:GEN:RFO:STAT ON; *OPC?')
            self.instr.query('CONF:SETT:RF; *OPC?')
            self.instr.query('CONF:SETT:NR5G; *OPC?')
            '''
            self.instr.query('SENS:ADJ:NCAN:AVER:STAT ON; *OPC?')
            self.instr.query(f'SENS:ADJ:NCAN:AVER:COUN {avg}; *OPC?')
            self.instr.query('INIT:IMM; *OPC?')
            k575_evm = self.queryFloat('FETC:CC1:ISRC:FRAM:SUMM:EVM:ALL:AVERage?')
            evm_measure_time = time() - start_time
            start_time = time()
            self.instr.write('CONF:NR5G:MEAS ACLR')
            self.instr.query('SENS:POW:NCOR ON; *OPC?')
            self.instr.write('INIT:IMM;*WAI')
            aclr_list = self.instr.query('CALC:MARK:FUNC:POW:RES? ACP')
            k575_chan_pow = float(aclr_list.split(',')[0])
            k575_adj_lower = float(aclr_list.split(',')[1])
            k575_adj_upper = float(aclr_list.split(',')[2])
            k575_aclr_time = time() - start_time
            self.instr.write('CONF:NR5G:MEAS EVM')
            self.instr.query('SENS:ADJ:NCAN:AVER:STAT OFF; *OPC?')
            logger.info(f"K575 EVM measurement with {avg} averages: EVM={k575_evm}, Time={evm_measure_time}, "
                        f"Channel Power={k575_chan_pow}, Lower Adjacent={k575_adj_lower}, Upper Adjacent={k575_adj_upper}, ACLR Time={k575_aclr_time}")
            return k575_evm, evm_measure_time, k575_chan_pow, k575_adj_lower, k575_adj_upper, k575_aclr_time
        except Exception as e:
            logger.error(f"K575 EVM measurement failed: {str(e)}")
            raise