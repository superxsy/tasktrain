#!/usr/bin/env python3
"""
Mouse Three-Key Sequence Task (Text-based version)
A behavioral experiment program for training mice on sequential button pressing tasks.
This version uses text interface instead of pygame for demonstration purposes.

Author: Behavioral Experiment Engineer
Version: 1.0 (Text Interface)
Requires: Python 3.10+ (no external dependencies)
"""

import json
import time
import os
import csv
import random
import threading
import sys
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Result codes
RESULT_CORRECT = 0
RESULT_NO_PRESS = 1
RESULT_WRONG_BUTTON = 2
RESULT_HOLD_TOO_LONG = 3
RESULT_PREMATURE_PRESS = 4

RESULT_TEXTS = {
    RESULT_CORRECT: "Correct",
    RESULT_NO_PRESS: "No Press",
    RESULT_WRONG_BUTTON: "Wrong Button",
    RESULT_HOLD_TOO_LONG: "Hold Too Long",
    RESULT_PREMATURE_PRESS: "Premature Press"
}

class TaskState(Enum):
    """State machine states for the task"""
    ITI = "ITI"
    L1_WAIT = "L1_WAIT"
    I1 = "I1"
    L2_WAIT = "L2_WAIT"
    I2 = "I2"
    L3_WAIT = "L3_WAIT"
    REWARD = "REWARD"
    SHAPING_WAIT = "SHAPING_WAIT"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"

@dataclass
class Config:
    """Configuration parameters for the task"""
    # Task mode
    mode: str = "sequence3"  # "sequence3" or "shaping1"
    shaping_led: int = 1  # 1, 2, or 3
    
    # Timing parameters (seconds)
    wait_L1: float = 3.0
    wait_L2: float = 3.0
    wait_L3: float = 3.0
    I1: float = 0.5
    I2: float = 0.5
    R_duration: float = 0.3
    release_window: float = 1.0
    
    # ITI parameters
    ITI_fixed_correct: float = 1.0
    ITI_rand_correct: float = 1.0
    ITI_fixed_error: float = 2.0
    ITI_rand_error: float = 1.0
    
    # Session parameters
    max_trials: int = 500
    subject_id: str = "M001"
    session_label: str = ""
    
    # Key mappings
    key_B1: str = "j"
    key_B2: str = "k"
    key_B3: str = "l"
    
    # Adaptive parameters
    adaptive_enabled: bool = False
    adaptive_window: int = 20
    adaptive_threshold_high: float = 0.85
    adaptive_threshold_low: float = 0.60
    adaptive_step: float = 0.1
    min_wait: float = 1.0
    max_wait: float = 5.0
    
    # Random seed
    rng_seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        return cls(**data)

class KeyboardInput:
    """Handle keyboard input in a separate thread"""
    
    def __init__(self):
        self.key_events = []
        self.running = True
        self.lock = threading.Lock()
    
    def start_input_thread(self):
        """Start keyboard input thread"""
        def input_worker():
            while self.running:
                try:
                    key = input().strip().lower()
                    timestamp = time.perf_counter()
                    with self.lock:
                        self.key_events.append({
                            'type': 'keypress',
                            'key': key,
                            'timestamp': timestamp
                        })
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
        
        thread = threading.Thread(target=input_worker, daemon=True)
        thread.start()
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get and clear pending events"""
        with self.lock:
            events = self.key_events.copy()
            self.key_events.clear()
            return events
    
    def stop(self):
        """Stop input thread"""
        self.running = False

class IOBackend:
    """Abstract hardware interface for future DAQ integration"""
    
    def set_led(self, led_index: int, on: bool) -> None:
        """Set LED state (1-3)"""
        pass
    
    def trigger_reward(self, duration: float) -> None:
        """Trigger reward delivery"""
        pass
    
    def process_events(self) -> List[Dict[str, Any]]:
        """Process and return input events"""
        return []

class TextBackend(IOBackend):
    """Text-based implementation of IO backend"""
    
    def __init__(self, config: Config):
        self.config = config
        self.led_states = [False, False, False]  # L1, L2, L3
        self.reward_active = False
        self.keyboard = KeyboardInput()
        self.keyboard.start_input_thread()
        
    def set_led(self, led_index: int, on: bool) -> None:
        """Set LED state (1-3)"""
        if 1 <= led_index <= 3:
            self.led_states[led_index - 1] = on
    
    def trigger_reward(self, duration: float) -> None:
        """Trigger reward delivery"""
        self.reward_active = True
    
    def stop_reward(self) -> None:
        """Stop reward delivery"""
        self.reward_active = False
    
    def process_events(self) -> List[Dict[str, Any]]:
        """Process keyboard events"""
        events = []
        key_events = self.keyboard.get_events()
        
        for event in key_events:
            key = event['key']
            
            # Handle special commands
            if key == 'quit' or key == 'q':
                events.append({'type': 'quit'})
            elif len(key) == 1:  # Single character keys
                events.append({
                    'type': 'keydown',
                    'key': key,
                    'timestamp': event['timestamp']
                })
                # Simulate immediate keyup for text interface
                events.append({
                    'type': 'keyup',
                    'key': key,
                    'timestamp': event['timestamp'] + 0.1
                })
            else:
                # Multi-character commands
                events.append({
                    'type': 'command',
                    'command': key,
                    'timestamp': event['timestamp']
                })
        
        return events
    
    def stop(self):
        """Stop the backend"""
        self.keyboard.stop()

class TrialLogger:
    """Handles trial data logging"""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_dir = os.path.join("data", config.subject_id, config.session_label)
        self.ensure_data_dir()
        self.session_csv_path = os.path.join(self.data_dir, "session_summary.csv")
        self.init_session_csv()
    
    def ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception as e:
            print(f"ERROR: Failed to create data directory: {e}")
    
    def init_session_csv(self) -> None:
        """Initialize session summary CSV file"""
        try:
            if not os.path.exists(self.session_csv_path):
                with open(self.session_csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'trial_index', 'mode', 'result_code', 'result_text',
                        'wait_L1', 'wait_L2', 'wait_L3', 'I1', 'I2', 'R_duration',
                        'release_window', 'press_times', 'release_times',
                        'reward_onset', 'reward_offset', 'iti_duration_actual',
                        'trial_start_walltime_iso'
                    ])
        except Exception as e:
            print(f"ERROR: Failed to initialize session CSV: {e}")
    
    def log_trial(self, trial_data: Dict[str, Any]) -> None:
        """Log trial data to both JSON and CSV"""
        try:
            # Save trial JSON
            trial_index = trial_data['trial_index']
            json_path = os.path.join(self.data_dir, f"trial_{trial_index:04d}.json")
            with open(json_path, 'w') as f:
                json.dump(trial_data, f, indent=2)
            
            # Append to session CSV
            with open(self.session_csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                press_times = ','.join(map(str, trial_data.get('press_release_times', {}).get('press_times', [])))
                release_times = ','.join(map(str, trial_data.get('press_release_times', {}).get('release_times', [])))
                
                writer.writerow([
                    trial_data['trial_index'],
                    trial_data['mode'],
                    trial_data['result_code'],
                    trial_data['result_text'],
                    trial_data['config_snapshot']['wait_L1'],
                    trial_data['config_snapshot']['wait_L2'],
                    trial_data['config_snapshot']['wait_L3'],
                    trial_data['config_snapshot']['I1'],
                    trial_data['config_snapshot']['I2'],
                    trial_data['config_snapshot']['R_duration'],
                    trial_data['config_snapshot']['release_window'],
                    press_times,
                    release_times,
                    trial_data.get('reward_onset', ''),
                    trial_data.get('reward_offset', ''),
                    trial_data.get('iti_duration_actual', ''),
                    trial_data['trial_start_walltime_iso']
                ])
        except Exception as e:
            print(f"ERROR: Failed to log trial {trial_data.get('trial_index', 'unknown')}: {e}")

class TaskStateMachine:
    """State machine for the behavioral task"""
    
    def __init__(self, config: Config, io_backend: IOBackend, logger: TrialLogger):
        self.config = config
        self.io_backend = io_backend
        self.logger = logger
        
        # State management
        self.state = TaskState.ITI
        self.state_start_time = 0.0
        self.session_start_time = time.perf_counter()
        
        # Trial management
        self.trial_index = 0
        self.trial_start_time = 0.0
        self.trial_events = []
        self.trial_result_code = None
        self.trial_result_text = ""
        
        # Press/release tracking
        self.current_press_time = None
        self.current_release_time = None
        self.press_release_times = {'press_times': [], 'release_times': []}
        
        # Timing
        self.iti_duration = 0.0
        self.reward_start_time = 0.0
        
        # Statistics
        self.trial_results = []  # List of result codes
        self.stats = {
            RESULT_CORRECT: 0,
            RESULT_NO_PRESS: 0,
            RESULT_WRONG_BUTTON: 0,
            RESULT_HOLD_TOO_LONG: 0,
            RESULT_PREMATURE_PRESS: 0
        }
        
        # Session control
        self.paused = False
        self.finished = False
        
        # Initialize random seed
        if config.rng_seed is not None:
            random.seed(config.rng_seed)
    
    def get_current_time(self) -> float:
        """Get current time relative to session start"""
        return time.perf_counter() - self.session_start_time
    
    def get_state_duration(self) -> float:
        """Get duration in current state"""
        return time.perf_counter() - self.state_start_time
    
    def enter_state(self, new_state: TaskState) -> None:
        """Enter a new state"""
        self.state = new_state
        self.state_start_time = time.perf_counter()
        
        # Log state entry
        self.trial_events.append({
            'type': 'state_enter',
            'state': new_state.value,
            'timestamp': self.get_current_time()
        })
        
        # State-specific entry logic
        if new_state == TaskState.ITI:
            self._enter_iti()
        elif new_state in [TaskState.L1_WAIT, TaskState.L2_WAIT, TaskState.L3_WAIT, TaskState.SHAPING_WAIT]:
            self._enter_wait_state(new_state)
        elif new_state == TaskState.REWARD:
            self._enter_reward()
    
    def _enter_iti(self) -> None:
        """Enter ITI state"""
        # Turn off all LEDs
        for i in range(1, 4):
            self.io_backend.set_led(i, False)
        
        # Calculate ITI duration
        if self.trial_result_code == RESULT_CORRECT:
            self.iti_duration = (self.config.ITI_fixed_correct + 
                               random.uniform(0, self.config.ITI_rand_correct))
        else:
            self.iti_duration = (self.config.ITI_fixed_error + 
                               random.uniform(0, self.config.ITI_rand_error))
    
    def _enter_wait_state(self, state: TaskState) -> None:
        """Enter a waiting state (L1, L2, L3, or SHAPING)"""
        # Turn on appropriate LED
        if state == TaskState.L1_WAIT:
            self.io_backend.set_led(1, True)
        elif state == TaskState.L2_WAIT:
            self.io_backend.set_led(2, True)
        elif state == TaskState.L3_WAIT:
            self.io_backend.set_led(3, True)
        elif state == TaskState.SHAPING_WAIT:
            self.io_backend.set_led(self.config.shaping_led, True)
        
        # Reset press/release tracking for this stage
        self.current_press_time = None
        self.current_release_time = None
    
    def _enter_reward(self) -> None:
        """Enter reward state"""
        # Turn off all LEDs
        for i in range(1, 4):
            self.io_backend.set_led(i, False)
        
        # Start reward
        self.io_backend.trigger_reward(self.config.R_duration)
        self.reward_start_time = time.perf_counter()
        
        # Log reward
        self.trial_events.append({
            'type': 'reward_on',
            'timestamp': self.get_current_time()
        })
    
    def start_new_trial(self) -> None:
        """Start a new trial"""
        self.trial_index += 1
        self.trial_start_time = time.perf_counter()
        self.trial_events = []
        self.trial_result_code = None
        self.trial_result_text = ""
        self.press_release_times = {'press_times': [], 'release_times': []}
        
        # Log trial start
        self.trial_events.append({
            'type': 'trial_start',
            'timestamp': self.get_current_time()
        })
        
        # Enter first state based on mode
        if self.config.mode == "shaping1":
            self.enter_state(TaskState.SHAPING_WAIT)
        else:
            self.enter_state(TaskState.L1_WAIT)
    
    def end_trial(self, result_code: int, result_text: str) -> None:
        """End current trial with result"""
        self.trial_result_code = result_code
        self.trial_result_text = result_text
        
        # Update statistics
        self.trial_results.append(result_code)
        self.stats[result_code] += 1
        
        # Log trial end
        self.trial_events.append({
            'type': 'trial_end',
            'result_code': result_code,
            'result_text': result_text,
            'timestamp': self.get_current_time()
        })
        
        # Log trial data
        trial_data = {
            'subject_id': self.config.subject_id,
            'session_label': self.config.session_label,
            'trial_index': self.trial_index,
            'mode': self.config.mode,
            'config_snapshot': self.config.to_dict(),
            'trial_start_walltime_iso': datetime.now().isoformat(),
            'trial_start_monotonic': self.trial_start_time - self.session_start_time,
            'events': self.trial_events,
            'press_release_times': self.press_release_times,
            'result_code': result_code,
            'result_text': result_text,
            'reward_duration_actual': self.config.R_duration if result_code == RESULT_CORRECT else 0,
            'iti_duration_actual': self.iti_duration
        }
        
        self.logger.log_trial(trial_data)
        
        # Enter ITI
        self.enter_state(TaskState.ITI)
    
    def process_key_event(self, event: Dict[str, Any]) -> None:
        """Process keyboard events"""
        key = event['key']
        timestamp = event['timestamp']
        
        # Log the event
        self.trial_events.append({
            'type': event['type'],
            'key': key,
            'timestamp': self.get_current_time()
        })
        
        if event['type'] == 'keydown':
            self._handle_keydown(key, timestamp)
        elif event['type'] == 'keyup':
            self._handle_keyup(key, timestamp)
    
    def _handle_keydown(self, key: str, timestamp: float) -> None:
        """Handle key press events"""
        # Check for task buttons
        task_keys = [self.config.key_B1, self.config.key_B2, self.config.key_B3]
        
        if key in task_keys:
            button_index = task_keys.index(key) + 1  # 1, 2, or 3
            
            # Check if we're in a valid state for button presses
            if self.state in [TaskState.ITI, TaskState.I1, TaskState.I2, TaskState.REWARD]:
                # Premature press
                self.end_trial(RESULT_PREMATURE_PRESS, "Premature Press")
                return
            
            # Check if correct button for current state
            expected_button = None
            if self.state == TaskState.L1_WAIT:
                expected_button = 1
            elif self.state == TaskState.L2_WAIT:
                expected_button = 2
            elif self.state == TaskState.L3_WAIT:
                expected_button = 3
            elif self.state == TaskState.SHAPING_WAIT:
                expected_button = self.config.shaping_led
            
            if expected_button is None:
                return  # Not in a waiting state
            
            if button_index != expected_button:
                # Wrong button
                self.end_trial(RESULT_WRONG_BUTTON, "Wrong Button")
                return
            
            # Correct button pressed
            self.current_press_time = timestamp
            self.press_release_times['press_times'].append(self.get_current_time())
    
    def _handle_keyup(self, key: str, timestamp: float) -> None:
        """Handle key release events"""
        # Check for task buttons
        task_keys = [self.config.key_B1, self.config.key_B2, self.config.key_B3]
        
        if key in task_keys and self.current_press_time is not None:
            button_index = task_keys.index(key) + 1
            
            # Check if this is the expected button release
            expected_button = None
            if self.state == TaskState.L1_WAIT:
                expected_button = 1
            elif self.state == TaskState.L2_WAIT:
                expected_button = 2
            elif self.state == TaskState.L3_WAIT:
                expected_button = 3
            elif self.state == TaskState.SHAPING_WAIT:
                expected_button = self.config.shaping_led
            
            if button_index == expected_button:
                self.current_release_time = timestamp
                self.press_release_times['release_times'].append(self.get_current_time())
                
                # Check release timing
                wait_duration = self._get_current_wait_duration()
                stage_end_time = self.state_start_time + wait_duration
                release_deadline = stage_end_time + self.config.release_window
                
                if timestamp <= release_deadline:
                    # Valid release - advance to next stage
                    self._advance_to_next_stage()
                else:
                    # Release too late
                    self.end_trial(RESULT_HOLD_TOO_LONG, "Hold Too Long")
    
    def _get_current_wait_duration(self) -> float:
        """Get the wait duration for the current state"""
        if self.state == TaskState.L1_WAIT:
            return self.config.wait_L1
        elif self.state == TaskState.L2_WAIT:
            return self.config.wait_L2
        elif self.state == TaskState.L3_WAIT:
            return self.config.wait_L3
        elif self.state == TaskState.SHAPING_WAIT:
            if self.config.shaping_led == 1:
                return self.config.wait_L1
            elif self.config.shaping_led == 2:
                return self.config.wait_L2
            else:
                return self.config.wait_L3
        return 0.0
    
    def _advance_to_next_stage(self) -> None:
        """Advance to the next stage after successful button press/release"""
        if self.state == TaskState.L1_WAIT:
            self.io_backend.set_led(1, False)
            self.enter_state(TaskState.I1)
        elif self.state == TaskState.L2_WAIT:
            self.io_backend.set_led(2, False)
            self.enter_state(TaskState.I2)
        elif self.state == TaskState.L3_WAIT or self.state == TaskState.SHAPING_WAIT:
            if self.state == TaskState.L3_WAIT:
                self.io_backend.set_led(3, False)
            else:
                self.io_backend.set_led(self.config.shaping_led, False)
            self.enter_state(TaskState.REWARD)
    
    def update(self) -> None:
        """Update state machine"""
        if self.paused or self.finished:
            return
        
        current_time = time.perf_counter()
        state_duration = current_time - self.state_start_time
        
        # State-specific updates
        if self.state == TaskState.ITI:
            if state_duration >= self.iti_duration:
                if self.trial_index >= self.config.max_trials:
                    self.finished = True
                    self.enter_state(TaskState.FINISHED)
                else:
                    self.start_new_trial()
        
        elif self.state in [TaskState.L1_WAIT, TaskState.L2_WAIT, TaskState.L3_WAIT, TaskState.SHAPING_WAIT]:
            wait_duration = self._get_current_wait_duration()
            if state_duration >= wait_duration:
                if self.current_press_time is None:
                    # No press within window
                    self.end_trial(RESULT_NO_PRESS, "No Press")
        
        elif self.state == TaskState.I1:
            if state_duration >= self.config.I1:
                self.enter_state(TaskState.L2_WAIT)
        
        elif self.state == TaskState.I2:
            if state_duration >= self.config.I2:
                self.enter_state(TaskState.L3_WAIT)
        
        elif self.state == TaskState.REWARD:
            if state_duration >= self.config.R_duration:
                self.io_backend.stop_reward()
                self.trial_events.append({
                    'type': 'reward_off',
                    'timestamp': self.get_current_time()
                })
                self.end_trial(RESULT_CORRECT, "Correct")
    
    def toggle_pause(self) -> None:
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            self.enter_state(TaskState.PAUSED)
    
    def reset_session(self) -> None:
        """Reset session statistics"""
        self.trial_index = 0
        self.trial_results = []
        self.stats = {code: 0 for code in self.stats}
        self.session_start_time = time.perf_counter()
        self.finished = False
        self.paused = False
        self.enter_state(TaskState.ITI)

def load_config() -> Config:
    """Load configuration from file or create default"""
    config_path = "config.json"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            config = Config.from_dict(data)
            print(f"Loaded configuration from {config_path}")
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            config = Config()
    else:
        config = Config()
        # Generate session label
        config.session_label = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save default config
        try:
            with open(config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            print(f"Created default configuration: {config_path}")
        except Exception as e:
            print(f"Warning: Could not save default config: {e}")
    
    # Ensure session label is set
    if not config.session_label:
        config.session_label = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return config

def display_status(state_machine, io_backend):
    """Display current status"""
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    
    print("=" * 60)
    print("MOUSE THREE-KEY SEQUENCE TASK (Text Interface)")
    print("=" * 60)
    print()
    
    # Session info
    print(f"Subject: {state_machine.config.subject_id}")
    print(f"Session: {state_machine.config.session_label}")
    print(f"Mode: {state_machine.config.mode.upper()}")
    print(f"Trial: {state_machine.trial_index}/{state_machine.config.max_trials}")
    print()
    
    # Current state
    print(f"Current State: {state_machine.state.value}")
    if state_machine.state != TaskState.ITI:
        remaining = get_remaining_time(state_machine)
        print(f"Remaining Time: {remaining:.1f}s")
    else:
        remaining = state_machine.iti_duration - state_machine.get_state_duration()
        print(f"ITI Remaining: {max(0, remaining):.1f}s")
    print()
    
    # LEDs
    led_status = []
    for i in range(3):
        status = "ON" if io_backend.led_states[i] else "OFF"
        led_status.append(f"L{i+1}: {status}")
    print("LEDs: " + " | ".join(led_status))
    
    # Reward
    reward_status = "ACTIVE" if io_backend.reward_active else "INACTIVE"
    print(f"Reward: {reward_status}")
    print()
    
    # Statistics
    total_trials = sum(state_machine.stats.values())
    accuracy = (state_machine.stats[RESULT_CORRECT] / max(1, total_trials)) * 100
    
    print("STATISTICS:")
    print(f"Total Trials: {total_trials}")
    print(f"Correct: {state_machine.stats[RESULT_CORRECT]} ({accuracy:.1f}%)")
    print(f"Errors: No Press={state_machine.stats[RESULT_NO_PRESS]}, "
          f"Wrong Button={state_machine.stats[RESULT_WRONG_BUTTON]}, "
          f"Hold Too Long={state_machine.stats[RESULT_HOLD_TOO_LONG]}, "
          f"Premature={state_machine.stats[RESULT_PREMATURE_PRESS]}")
    print()
    
    # Recent results
    recent_results = state_machine.trial_results[-10:]
    if recent_results:
        print(f"Recent Results (last {len(recent_results)}): {recent_results}")
        print()
    
    # Parameters
    print("CURRENT PARAMETERS:")
    print(f"Wait Times: L1={state_machine.config.wait_L1:.1f}s, "
          f"L2={state_machine.config.wait_L2:.1f}s, L3={state_machine.config.wait_L3:.1f}s")
    print(f"Intervals: I1={state_machine.config.I1:.1f}s, I2={state_machine.config.I2:.1f}s")
    print(f"Release Window: {state_machine.config.release_window:.1f}s")
    print(f"Reward Duration: {state_machine.config.R_duration:.1f}s")
    print()
    
    # Controls
    print("CONTROLS:")
    print(f"Task Buttons: {state_machine.config.key_B1.upper()}, "
          f"{state_machine.config.key_B2.upper()}, {state_machine.config.key_B3.upper()}")
    print("Commands: 'start' (begin session), 'pause' (pause/resume), 'reset' (reset session)")
    print("          'mode' (switch mode), 'help' (show help), 'quit' (exit)")
    print()
    
    if state_machine.paused:
        print("*** PAUSED ***")
        print()
    
    if state_machine.finished:
        print("*** SESSION FINISHED ***")
        print()
    
    print("Enter command or key:")

def get_remaining_time(state_machine) -> float:
    """Get remaining time for current state"""
    state_duration = state_machine.get_state_duration()
    
    if state_machine.state == TaskState.L1_WAIT:
        return max(0, state_machine.config.wait_L1 - state_duration)
    elif state_machine.state == TaskState.L2_WAIT:
        return max(0, state_machine.config.wait_L2 - state_duration)
    elif state_machine.state == TaskState.L3_WAIT:
        return max(0, state_machine.config.wait_L3 - state_duration)
    elif state_machine.state == TaskState.SHAPING_WAIT:
        wait_time = getattr(state_machine.config, f"wait_L{state_machine.config.shaping_led}")
        return max(0, wait_time - state_duration)
    elif state_machine.state == TaskState.I1:
        return max(0, state_machine.config.I1 - state_duration)
    elif state_machine.state == TaskState.I2:
        return max(0, state_machine.config.I2 - state_duration)
    elif state_machine.state == TaskState.REWARD:
        return max(0, state_machine.config.R_duration - state_duration)
    else:
        return 0.0

def show_help():
    """Show help information"""
    print("\n" + "=" * 60)
    print("HELP - MOUSE THREE-KEY SEQUENCE TASK")
    print("=" * 60)
    print()
    print("TASK MODES:")
    print("  Sequence-3: Complete sequence L1→I1→L2→I2→L3→Reward")
    print("  Shaping-1: Single LED press for reward")
    print()
    print("CONTROLS:")
    print("  Task Keys: j, k, l (for buttons B1, B2, B3)")
    print("  Commands:")
    print("    'start' - Start the session")
    print("    'pause' - Pause/resume session")
    print("    'reset' - Reset session statistics")
    print("    'mode'  - Switch between sequence3 and shaping1")
    print("    'help'  - Show this help")
    print("    'quit'  - Exit program")
    print()
    print("RESULT CODES:")
    print("  0 - Correct: Successful completion")
    print("  1 - No Press: Failed to press within time window")
    print("  2 - Wrong Button: Pressed incorrect button")
    print("  3 - Hold Too Long: Failed to release within release window")
    print("  4 - Premature Press: Pressed button at wrong time")
    print()
    print("RELEASE LOGIC:")
    print("  1. Press correct button during LED wait period")
    print("  2. Release button within 'release window' after wait period ends")
    print("  3. If you press too early or hold too long, trial fails")
    print()
    print("Press Enter to continue...")
    input()

def main():
    """Main program loop"""
    print("Mouse Three-Key Sequence Task (Text Interface)")
    print("===============================================")
    
    # Load configuration
    config = load_config()
    
    print(f"Subject ID: {config.subject_id}")
    print(f"Session: {config.session_label}")
    print(f"Mode: {config.mode}")
    print(f"Data directory: data/{config.subject_id}/{config.session_label}/")
    print()
    
    # Initialize components
    io_backend = TextBackend(config)
    logger = TrialLogger(config)
    state_machine = TaskStateMachine(config, io_backend, logger)
    
    # Main loop
    running = True
    session_started = False
    last_display_time = 0
    
    try:
        while running:
            current_time = time.time()
            
            # Update display every 0.5 seconds
            if current_time - last_display_time > 0.5:
                display_status(state_machine, io_backend)
                last_display_time = current_time
            
            # Process events
            events = io_backend.process_events()
            
            for event in events:
                if event['type'] == 'quit':
                    running = False
                
                elif event['type'] == 'command':
                    command = event['command']
                    
                    if command == 'start':
                        if not session_started:
                            session_started = True
                            state_machine.start_new_trial()
                            print("Session started!")
                        else:
                            print("Session already started. Use 'pause' to pause/resume.")
                    
                    elif command == 'pause':
                        if session_started:
                            state_machine.toggle_pause()
                            print("Paused" if state_machine.paused else "Resumed")
                        else:
                            print("No session to pause. Use 'start' first.")
                    
                    elif command == 'reset':
                        state_machine.reset_session()
                        session_started = False
                        print("Session reset")
                    
                    elif command == 'mode':
                        config.mode = "shaping1" if config.mode == "sequence3" else "sequence3"
                        print(f"Switched to {config.mode} mode")
                        if session_started:
                            state_machine.reset_session()
                            session_started = False
                    
                    elif command == 'help':
                        show_help()
                    
                    elif command == 'quit':
                        running = False
                    
                    else:
                        print(f"Unknown command: {command}")
                
                elif event['type'] in ['keydown', 'keyup']:
                    # Pass task-related events to state machine
                    if session_started and not state_machine.paused:
                        state_machine.process_key_event(event)
            
            # Update state machine
            if session_started:
                state_machine.update()
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        io_backend.stop()
        print(f"\nSession ended. Data saved to: {logger.data_dir}")

if __name__ == "__main__":
    main()

"""
TEXT INTERFACE TESTING GUIDE
============================

This text-based version demonstrates all the core functionality of the mouse sequence task
without requiring pygame. Here's how to test it:

1. SETUP:
   - Run: python mouse_sequence_task_text.py
   - The program will show a text interface with current status

2. BASIC CONTROLS:
   - Type 'start' and press Enter to begin session
   - Type 'help' for detailed help information
   - Type 'quit' to exit

3. TESTING SEQUENCE:
   a) Start session with 'start'
   b) When L1 LED shows "ON", type 'j' and press Enter
   c) Wait for I1 interval, then L2 will turn on
   d) Type 'k' when L2 is on
   e) Wait for I2 interval, then L3 will turn on
   f) Type 'l' when L3 is on
   g) Should see reward and result code 0

4. ERROR TESTING:
   - No press: Don't press anything when LED is on
   - Wrong button: Press 'k' when L1 is on
   - Premature press: Press any task key during ITI

5. MODE SWITCHING:
   - Type 'mode' to switch between sequence3 and shaping1
   - In shaping1, only one LED will be active

6. DATA VERIFICATION:
   - Check data/{subject_id}/{session_label}/ for trial files
   - Each trial creates a JSON file with detailed timing
   - session_summary.csv contains trial summaries

NOTE: This text interface simulates immediate key release after press,
so the "hold too long" error is harder to test. The pygame version
provides full press/release timing control.
"""