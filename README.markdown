# RF Measurement Project

## Overview
This project provides Python scripts to control a Vector Signal Analyzer (VSA) and Vector Signal Generator (VSG) for RF measurements, supporting LTE, 5G NR, Sub-Thermal Noise (STN), and Spur Search tests. Test parameters and execution flags are defined in a JSON configuration file (`config/test_inputs.json`). Results are saved as JSON (`results_output.json`) and Excel (`results_output.xlsx`) files.

## Project Structure
```
Qorvo_STNoise_LTE_5GNR_meas_with_timing/
├── src/                     # Source code
│   ├── instruments/         # Instrument control classes and configuration
│   │   ├── iSocket.py      # Custom socket communication library
│   │   ├── bench_config.ini # Instrument IP configuration
│   ├── measurements/        # Measurement driver scripts
│   ├── utils/               # Utility functions
│   ├── main.py              # Main script to run measurements
├── config/                  # Configuration files
│   ├── test_inputs.json     # User-defined test parameters and flags
│   ├── bench_config.ini     # Instrument IP settings
├── tests/                   # Unit tests for validation
├── scripts/                 # Automation scripts (planned, currently empty)
├── logs/                    # Log files generated during execution
├── docs/                    # Project documentation
├── requirements.txt         # Python dependencies
├── setup.bat                # Windows setup script
├── .gitignore               # Git ignore rules
├── .gitattributes           # Git attributes
└── pyproject.toml           # Project metadata (optional)
```

## Setup

### Prerequisites
- Python 3.8 or higher
- Network-accessible VSA and VSG instruments

### Install Dependencies
```bash
pip install -r requirements.txt
```
The `iSocket` library is included in `src/instruments/iSocket.py`. Alternatively, you can use `pyvisa` for instrument communication.

### Configure Instruments
1. Update `config/bench_config.ini` with the IP addresses of your VSA and VSG.
   ```ini
   [Settings]
   VSA_IP = 192.168.200.20
   VSG_IP = 192.168.200.10
   ```

### Configure Test Parameters
1. Edit `config/test_inputs.json` to define test parameters for LTE, 5G NR, STN, and Spur Search. The file contains four sections:
   - `lte`: LTE signal measurements
   - `nr5g`: 5G NR (FR1) measurements
   - `STN`: Sub-Thermal Noise measurements
   - `spur_search`: Spur detection
2. Example configuration:
   ```json
   {
     "lte": [
       {
         "run": true,
         "center_frequency_ghz": [6.201, 6.501],
         "power_dbm": [-10.0, -9.0, -8.0, -7.0, -6.0, -5.0],
         "resource_block_offset": 0,
         "channel_bandwidth_mhz": 5,
         "modulation_type": "QPSK",
         "duplexing": "TDD",
         "link_direction": "UL",
         "measure_ch_pwr": true,
         "measure_aclr": true
       }
     ],
     "nr5g": [
       {
         "run": true,
         "center_frequency_ghz": [6.123, 6.223],
         "power_dbm": [-5.0, -1.0],
         "resource_blocks": 51,
         "resource_block_offset": 0,
         "channel_bandwidth_mhz": 20,
         "modulation_type": "QAM256",
         "subcarrier_spacing_khz": 30,
         "measure_ch_pwr": true,
         "measure_aclr": true
       }
     ],
     "STN": [
       {
         "run": true,
         "center_frequency_ghz": {
           "range": {
             "start_ghz": 0.617,
             "stop_ghz": 0.961,
             "step_mhz": 10
           }
         },
         "iterations": 1
       },
       {
         "run": true,
         "center_frequency_ghz": [2.483, 3.300, 3.500],
         "iterations": 1
       }
     ],
     "spur_search": [
       {
         "run": true,
         "fundamental_frequency_ghz": 6.000,
         "rbw_mhz": 0.01,
         "spur_limit_dbm": -95,
         "power_dbm": -10.0
       }
     ]
   }
   ```
3. Notes on `test_inputs.json`:
   - **Frequencies**: Specify in GHz as single values, lists, or ranges (e.g., `{"range": {"start_ghz": 0.617, "stop_ghz": 0.961, "step_mhz": 10}}`).
   - **Power Inputs**: Use arrays for power sweeps (e.g., `[-10.0, -9.0, -8.0]`).
   - **Run Flags**: Set `"run": true` to enable a test; `false` to skip.
   - Multiple entries with `"run": true` enable frequency sweeps; power sweeps use `power_dbm` arrays.
   - Ensure numeric values for frequencies/powers and boolean flags.
   - Defaults are applied if the file is missing or malformed.
   - Save the file with UTF-8 encoding.

## Usage
Run the measurements using:
```bash
python src/main.py
```

### Supported Measurements
- **LTE Measurement**: Measures LTE signals if `"run": true` in the `lte` section.
- **5G NR Measurement**: Measures 5G NR (FR1) signals if `"run": true` in the `nr5g` section.
- **Sub-Thermal Noise (STN) Measurement**: Measures noise power if `"run": true` in the `STN` section.
- **Spur Search Measurement**: Detects spurs if `"run": true` in the `spur_search` section.

### Parameter Sweeps
- **Frequency Sweeps**: Use multiple entries or lists/ranges in `center_frequency_ghz`.
- **Power Sweeps**: Use arrays in `power_dbm`.

### Output
Results are saved to:
- `results_output.json`: Detailed measurement results in JSON format.
- `results_output.xlsx`: Results in Excel format for easy analysis.

## Requirements
- **Python**: 3.8+
- **Libraries**:
  - `numpy>=1.24.0`
  - `pandas>=2.0.0`
  - `openpyxl>=3.1.0`
  - `iSocket` (custom, included in `src/instruments/iSocket.py`)

## Notes
- Ensure VSA and VSG are network-accessible.
- Update SCPI commands in `src/instruments/` for different instrument models.
- Add unit tests in `tests/` for validation.
- Do not track generated files (`results_output.json`, `results_output.xlsx`) in version control (already in `.gitignore`).
- The `scripts/` directory is planned for future automation scripts.
- The `pyproject.toml` file is optional for project metadata.

## Contributing
Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
[Specify license, e.g., MIT License, or state "Proprietary" if applicable.]