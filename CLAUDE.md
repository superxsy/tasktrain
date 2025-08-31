
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run the program**: `python mouse_sequence_task.py`
- **Install dependencies**: `pip install pygame` (from `requirements.txt`)

## High-level Architecture

The project is a Python-based behavioral experiment program using Pygame to simulate a three-key sequence task for mice. It follows a strict state machine architecture for precise timing and data logging.

### Core Components:

- `mouse_sequence_task.py`: The main program file containing the core logic, state machine, UI, and I/O backend.
- `config.json`: JSON file for storing and loading configurable parameters such as timing, mode, and session settings.
- `data/`: Directory for storing experimental data, including detailed trial-level JSON files and session-level CSV summaries.
- `README.md`: Comprehensive documentation covering project overview, features, installation, usage, data recording, and technical architecture.

### Key Architectural Aspects:

- **State Machine**: The `TaskStateMachine` class manages the experimental flow through distinct states like `ITI`, `L1_WAIT`, `I1`, `L2_WAIT`, `I2`, `L3_WAIT`, `REWARD`, `SHAPING_WAIT`, `PAUSED`, and `FINISHED`. This ensures precise temporal control and event handling.
- **Modular I/O Backend**: The `IOBackend` abstract class and its `KeyboardScreenBackend` implementation decouple input/output (keyboard, screen, reward) from the core task logic, allowing for future integration with hardware like DAQ devices.
- **Configuration Management**: Parameters are loaded from `config.json` via the `Config` dataclass, supporting dynamic adjustment during the experiment via hotkeys and UI inputs, and logged as snapshots with each trial.
- **Data Logging**: The `TrialLogger` class handles the persistent storage of experimental data, generating detailed JSON files for each trial and a summary CSV file per session. This includes event timestamps, parameter snapshots, and performance statistics.
- **UI (Pygame)**: The `UI` class renders the real-time experimental interface, displaying current state, LED indicators, statistics, recent results, and interactive parameter input fields.
- **Adaptive Difficulty**: An optional adaptive mode adjusts task parameters (e.g., wait times) based on recent performance to maintain a target accuracy level.
- **Windows IME Handling**: Includes specific logic to manage Windows Input Method Editor (IME) to ensure proper key input during the experiment.