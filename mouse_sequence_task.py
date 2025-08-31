#!/usr/bin/env python3
"""
Mouse Three-Key Sequence Task
A behavioral experiment program for training mice on sequential button pressing tasks.

Author: Behavioral Experiment Engineer
Version: 1.0
Requires: Python 3.10+, pygame

MANUAL TESTING SCRIPT:
======================

1. SETUP:
   - Install pygame: pip install pygame
   - Run: python mouse_sequence_task.py
   - Program creates default config.json and data directory

2. BASIC SEQUENCE TESTING (Sequence-3 mode):
   a) Press SPACE to start session
   b) When L1 (leftmost circle) lights up, press and hold J
   c) Release J before the wait window + release window expires
   d) Wait for I1 interval, then L2 lights up
   e) Press and hold K, release before deadline
   f) Wait for I2 interval, then L3 lights up
   g) Press and hold L, release before deadline
   h) Should see reward indication and result code 0 (green)

3. ERROR CONDITION TESTING:
   a) No Press (Result 1): Don't press anything when LED is on
   b) Wrong Button (Result 2): Press K when L1 is on
   c) Hold Too Long (Result 3): Press correct button but don't release until after deadline
   d) Premature Press (Result 4): Press any task key during ITI or interval periods

4. SHAPING MODE TESTING:
   a) Press TAB to switch to Shaping-1 mode
   b) Only one LED will be active (configurable)
   c) Press corresponding button and release for immediate reward

5. PARAMETER ADJUSTMENT TESTING:
   a) Press H to show help overlay
   b) Press [ or ] to adjust current wait time
   c) Press - or = to adjust release window
   d) Verify changes are reflected in UI

6. DATA VERIFICATION:
   a) Check data/{subject_id}/{session_label}/ directory
   b) Verify trial_XXXX.json files contain detailed timing data
   c) Verify session_summary.csv matches trial results
   d) Check that result codes in files match UI display

7. ADAPTIVE MODE TESTING (if enabled in config):
   a) Complete several trials successfully
   b) Observe wait times automatically decreasing
   c) Make several errors and observe wait times increasing

8. SESSION CONTROL TESTING:
   a) Press SPACE to pause/resume
   b) Press R to reset session
   c) Press Q to quit and save data
"""

import pygame
import json
import time
import os
import csv
import random
import sys
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Windows IME handling
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        HAS_WIN32_IME = True
    except ImportError:
        HAS_WIN32_IME = False
else:
    HAS_WIN32_IME = False

def set_english_ime():
    """Set input method to English on Windows"""
    if not HAS_WIN32_IME:
        return False
    
    try:
        # Get the current window handle
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        # Get current thread ID
        thread_id = kernel32.GetCurrentThreadId()
        
        # Load English (US) keyboard layout
        # 0x04090409 is the identifier for English (US) keyboard layout
        english_layout = user32.LoadKeyboardLayoutW("00000409", 0)
        
        if english_layout:
            # Activate the English keyboard layout for current thread
            user32.ActivateKeyboardLayout(english_layout, 0)
            return True
        
        return False
    except Exception as e:
        print(f"Warning: Could not set English IME: {e}")
        return False

def disable_ime_for_pygame():
    """Disable IME for pygame window on Windows"""
    if not HAS_WIN32_IME:
        return False
    
    try:
        # Set environment variable to disable IME for SDL/pygame
        os.environ['SDL_IME_SHOW_UI'] = '0'
        return True
    except Exception as e:
        print(f"Warning: Could not disable IME for pygame: {e}")
        return False

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1980, 1280  # Custom large window size as requested
FPS = 60

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_LIGHT_GRAY = (200, 200, 200)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_ORANGE = (255, 165, 0)
COLOR_PURPLE = (128, 0, 128)
COLOR_DARK_GREEN = (0, 128, 0)

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

RESULT_COLORS = {
    RESULT_CORRECT: COLOR_GREEN,
    RESULT_NO_PRESS: COLOR_GRAY,
    RESULT_WRONG_BUTTON: COLOR_RED,
    RESULT_HOLD_TOO_LONG: COLOR_ORANGE,
    RESULT_PREMATURE_PRESS: COLOR_PURPLE
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
    
    # Visual parameters
    window_width: int = 1000
    window_height: int = 1000
    led_radius: int = 30
    
    # Random seed
    rng_seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        return cls(**data)

class IOBackend(ABC):
    """Abstract hardware interface for future DAQ integration"""
    
    @abstractmethod
    def set_led(self, led_index: int, on: bool) -> None:
        """Set LED state (1-3)"""
        pass
    
    @abstractmethod
    def trigger_reward(self, duration: float) -> None:
        """Trigger reward delivery"""
        pass
    
    @abstractmethod
    def process_events(self) -> List[Dict[str, Any]]:
        """Process and return input events"""
        pass

class KeyboardScreenBackend(IOBackend):
    """Pygame-based implementation of IO backend"""
    
    def __init__(self, config: Config):
        self.config = config
        self.led_states = [False, False, False]  # L1, L2, L3
        self.reward_active = False
        self.reward_end_time = 0.0
        
        # Key mapping
        self.key_map = {
            pygame.K_j: 'j',
            pygame.K_k: 'k',
            pygame.K_l: 'l',
            pygame.K_SPACE: 'space',
            pygame.K_q: 'q',
            pygame.K_r: 'r',
            pygame.K_TAB: 'tab',
            pygame.K_h: 'h',
            pygame.K_LEFTBRACKET: '[',
            pygame.K_RIGHTBRACKET: ']',
            pygame.K_MINUS: '-',
            pygame.K_EQUALS: '=',
            pygame.K_BACKSPACE: 'backspace',
            pygame.K_RETURN: 'return'
        }
    
    def set_led(self, led_index: int, on: bool) -> None:
        """Set LED state (1-3)"""
        if 1 <= led_index <= 3:
            self.led_states[led_index - 1] = on
    
    def trigger_reward(self, duration: float) -> None:
        """Trigger reward delivery"""
        self.reward_active = True
        self.reward_end_time = time.perf_counter() + duration
    
    def stop_reward(self) -> None:
        """Stop reward delivery"""
        self.reward_active = False
    
    def update_reward(self) -> None:
        """Update reward state based on timing"""
        if self.reward_active and time.perf_counter() >= self.reward_end_time:
            self.reward_active = False
    
    def _check_ime_and_retry(self) -> None:
        """Check if IME is causing issues and try to fix it"""
        if sys.platform == "win32" and HAS_WIN32_IME:
            try:
                # Try to switch to English layout if we detect potential IME issues
                set_english_ime()
            except Exception:
                pass  # Silently ignore errors
    
    def process_events(self) -> List[Dict[str, Any]]:
        """Process pygame events with IME handling"""
        events = []
        ime_issue_detected = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append({'type': 'quit'})
            
            elif event.type == pygame.KEYDOWN:
                if event.key in self.key_map:
                    key = self.key_map[event.key]
                    events.append({
                        'type': 'keydown',
                        'key': key,
                        'timestamp': time.perf_counter()
                    })
                else:
                    # Check if this might be an IME issue with JKL keys
                    if event.key in [pygame.K_j, pygame.K_k, pygame.K_l]:
                        ime_issue_detected = True
            
            elif event.type == pygame.KEYUP:
                if event.key in self.key_map:
                    key = self.key_map[event.key]
                    events.append({
                        'type': 'keyup',
                        'key': key,
                        'timestamp': time.perf_counter()
                    })
            
            elif event.type == pygame.TEXTINPUT:
                # Check if we're getting text input for JKL keys (indicates IME is active)
                if event.text.lower() in ['j', 'k', 'l']:
                    ime_issue_detected = True
                    # Convert text input to keydown event for JKL keys
                    key_mapping = {'j': 'j', 'k': 'k', 'l': 'l'}
                    if event.text.lower() in key_mapping:
                        events.append({
                            'type': 'keydown',
                            'key': key_mapping[event.text.lower()],
                            'timestamp': time.perf_counter()
                        })
                else:
                    events.append({
                        'type': 'textinput',
                        'text': event.text,
                        'timestamp': time.perf_counter()
                    })
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                events.append({
                    'type': 'mousebuttondown',
                    'button': event.button,
                    'pos': event.pos,
                    'timestamp': time.perf_counter()
                })
        
        # If IME issue detected, try to fix it
        if ime_issue_detected:
            self._check_ime_and_retry()
        
        # Update reward state
        self.update_reward()
        
        return events

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
            print(f"Data directory: {self.data_dir}")
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
        self.iti_error_recorded = False  # Flag to prevent multiple error recordings in ITI
        
        # Press/release tracking
        self.current_press_time = None
        self.current_release_time = None
        self.press_release_times = {'press_times': [], 'release_times': []}
        self.pressed_keys = set()  # Track currently pressed keys
        
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
        self.iti_errors = 0  # Separate counter for ITI errors
        self.iti_key_counts = {}  # Detailed ITI key press counts
        
        # Session control
        self.paused = False
        self.finished = False
        self.session_started = False
        
        # Adaptive adjustments log
        self.adaptive_adjustments = []
        
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
        
        # Reset ITI error flag
        self.iti_error_recorded = False
        
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
            self.trial_events.append({'type': 'led_on', 'led': 1, 'timestamp': self.get_current_time()})
        elif state == TaskState.L2_WAIT:
            self.io_backend.set_led(2, True)
            self.trial_events.append({'type': 'led_on', 'led': 2, 'timestamp': self.get_current_time()})
        elif state == TaskState.L3_WAIT:
            self.io_backend.set_led(3, True)
            self.trial_events.append({'type': 'led_on', 'led': 3, 'timestamp': self.get_current_time()})
        elif state == TaskState.SHAPING_WAIT:
            self.io_backend.set_led(self.config.shaping_led, True)
            self.trial_events.append({'type': 'led_on', 'led': self.config.shaping_led, 'timestamp': self.get_current_time()})
        
        # Reset press/release tracking for this stage
        self.current_press_time = None
        self.current_release_time = None
    
    def _enter_reward(self) -> None:
        """Enter reward state"""
        # Turn off all LEDs
        for i in range(1, 4):
            self.io_backend.set_led(i, False)
            self.trial_events.append({'type': 'led_off', 'led': i, 'timestamp': self.get_current_time()})
        
        # Start reward
        self.io_backend.trigger_reward(self.config.R_duration)
        self.reward_start_time = time.perf_counter()
        
        # Log reward
        self.trial_events.append({
            'type': 'reward_on',
            'timestamp': self.get_current_time()
        })
    
    def start_session(self) -> None:
        """Start the session"""
        if not self.session_started:
            self.session_started = True
            self.session_start_time = time.perf_counter()
            self.start_new_trial()
    
    def start_new_trial(self) -> None:
        """Start a new trial"""
        if not self.session_started:
            return
            
        self.trial_index += 1
        self.trial_start_time = time.perf_counter()
        self.trial_events = []
        self.trial_result_code = None
        self.trial_result_text = ""
        self.press_release_times = {'press_times': [], 'release_times': []}
        self.pressed_keys.clear()
        
        # Log trial start
        self.trial_events.append({
            'type': 'trial_start',
            'timestamp': self.get_current_time()
        })
        
        # Apply adaptive adjustments if enabled
        if self.config.adaptive_enabled:
            self._apply_adaptive_adjustments()
        
        # Enter first state based on mode
        if self.config.mode == "shaping1":
            self.enter_state(TaskState.SHAPING_WAIT)
        else:
            self.enter_state(TaskState.L1_WAIT)
    
    def _apply_adaptive_adjustments(self) -> None:
        """Apply adaptive difficulty adjustments based on recent performance"""
        if len(self.trial_results) < self.config.adaptive_window:
            return
        
        # Calculate recent performance
        recent_results = self.trial_results[-self.config.adaptive_window:]
        correct_count = sum(1 for r in recent_results if r == RESULT_CORRECT)
        accuracy = correct_count / len(recent_results)
        
        adjustment_made = False
        
        if accuracy >= self.config.adaptive_threshold_high:
            # Decrease wait times (make harder)
            for wait_param in ['wait_L1', 'wait_L2', 'wait_L3']:
                current_val = getattr(self.config, wait_param)
                new_val = max(self.config.min_wait, current_val - self.config.adaptive_step)
                if new_val != current_val:
                    setattr(self.config, wait_param, new_val)
                    adjustment_made = True
        
        elif accuracy <= self.config.adaptive_threshold_low:
            # Increase wait times (make easier)
            for wait_param in ['wait_L1', 'wait_L2', 'wait_L3']:
                current_val = getattr(self.config, wait_param)
                new_val = min(self.config.max_wait, current_val + self.config.adaptive_step)
                if new_val != current_val:
                    setattr(self.config, wait_param, new_val)
                    adjustment_made = True
        
        if adjustment_made:
            adjustment = {
                'trial_index': self.trial_index,
                'accuracy': accuracy,
                'wait_L1': self.config.wait_L1,
                'wait_L2': self.config.wait_L2,
                'wait_L3': self.config.wait_L3,
                'timestamp': self.get_current_time()
            }
            self.adaptive_adjustments.append(adjustment)
    
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
        
        # Add adaptive adjustments if any
        if self.adaptive_adjustments:
            trial_data['adaptive_adjustments'] = self.adaptive_adjustments[-1] if self.adaptive_adjustments else None
        
        self.logger.log_trial(trial_data)
        
        # Enter ITI
        self.enter_state(TaskState.ITI)
    
    def process_key_event(self, event: Dict[str, Any]) -> None:
        """Process keyboard events"""
        key = event['key']
        timestamp = event['timestamp']
        
        # Handle control keys (these work regardless of session state)
        if event['type'] == 'keydown':
            if key == 'space':
                if not self.session_started:
                    self.start_session()
                else:
                    self.toggle_pause()
                return
            elif key == 'r':
                self.reset_session()
                return
            elif key == 'tab':
                self.toggle_mode()
                return
            elif key == '[':
                self.adjust_current_wait_time(-0.1)
                return
            elif key == ']':
                self.adjust_current_wait_time(0.1)
                return
            elif key == '-':
                self.config.release_window = max(0.1, self.config.release_window - 0.1)
                return
            elif key == '=':
                self.config.release_window = min(5.0, self.config.release_window + 0.1)
                return
        
        # Only process task keys if session is active
        if not self.session_started or self.paused:
            return
        
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
            self.pressed_keys.add(key)
            
            # Check if we're in a valid state for button presses
            if self.state in [TaskState.ITI, TaskState.I1, TaskState.I2, TaskState.REWARD]:
                # For ITI state, only record error once per ITI period and don't reset ITI
                if self.state == TaskState.ITI:
                    if not self.iti_error_recorded:
                        self.iti_error_recorded = True
                        self.iti_errors += 1
                        # Log the ITI error event but don't end trial or reset ITI
                        self.trial_events.append({
                            'type': 'iti_error',
                            'key': key,
                            'timestamp': self.get_current_time()
                        })
                    
                    # Record detailed key counts for ITI
                    if key not in self.iti_key_counts:
                        self.iti_key_counts[key] = 0
                    self.iti_key_counts[key] += 1
                    
                    return  # Continue current ITI without resetting
                
                # For other invalid states (I1, I2, REWARD), end trial
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
            if self.current_press_time is None:  # Only record first press
                self.current_press_time = timestamp
                self.press_release_times['press_times'].append(self.get_current_time())
    
    def _handle_keyup(self, key: str, timestamp: float) -> None:
        """Handle key release events"""
        # Check for task buttons
        task_keys = [self.config.key_B1, self.config.key_B2, self.config.key_B3]
        
        if key in task_keys:
            self.pressed_keys.discard(key)
            button_index = task_keys.index(key) + 1
            
            # Check if this is the expected button release and we have a press time
            if self.current_press_time is None:
                return  # No corresponding press
            
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
                
                # Check release timing - CRITICAL LOGIC
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
    
    def _get_current_led_index(self) -> Optional[int]:
        """Get the LED index for the current state"""
        if self.state == TaskState.L1_WAIT:
            return 1
        elif self.state == TaskState.L2_WAIT:
            return 2
        elif self.state == TaskState.L3_WAIT:
            return 3
        elif self.state == TaskState.SHAPING_WAIT:
            return self.config.shaping_led
        return None
    
    def _advance_to_next_stage(self) -> None:
        """Advance to the next stage after successful button press/release"""
        if self.state == TaskState.L1_WAIT:
            self.io_backend.set_led(1, False)
            self.trial_events.append({'type': 'led_off', 'led': 1, 'timestamp': self.get_current_time()})
            self.enter_state(TaskState.I1)
        elif self.state == TaskState.L2_WAIT:
            self.io_backend.set_led(2, False)
            self.trial_events.append({'type': 'led_off', 'led': 2, 'timestamp': self.get_current_time()})
            self.enter_state(TaskState.I2)
        elif self.state == TaskState.L3_WAIT or self.state == TaskState.SHAPING_WAIT:
            if self.state == TaskState.L3_WAIT:
                self.io_backend.set_led(3, False)
                self.trial_events.append({'type': 'led_off', 'led': 3, 'timestamp': self.get_current_time()})
            else:
                self.io_backend.set_led(self.config.shaping_led, False)
                self.trial_events.append({'type': 'led_off', 'led': self.config.shaping_led, 'timestamp': self.get_current_time()})
            self.enter_state(TaskState.REWARD)
    
    def update(self) -> None:
        """Update state machine"""
        if self.paused or self.finished or not self.session_started:
            return
        
        current_time = time.perf_counter()
        state_duration = current_time - self.state_start_time
        
        # State-specific updates
        if self.state == TaskState.ITI:
            if state_duration >= self.iti_duration:
                # Check if any task buttons are currently pressed
                task_keys = [self.config.key_B1, self.config.key_B2, self.config.key_B3]
                any_pressed = any(key in self.pressed_keys for key in task_keys)
                
                if any_pressed:
                    # Wait until all buttons are released before starting next trial
                    return
                
                if self.trial_index >= self.config.max_trials:
                    self.finished = True
                    self.enter_state(TaskState.FINISHED)
                else:
                    self.start_new_trial()
        
        elif self.state in [TaskState.L1_WAIT, TaskState.L2_WAIT, TaskState.L3_WAIT, TaskState.SHAPING_WAIT]:
            wait_duration = self._get_current_wait_duration()
            
            # Check if button is pressed and holding time exceeds release window
            if self.current_press_time is not None:
                hold_duration = current_time - self.current_press_time
                
                # Release window starts from button press, not from wait duration
                if hold_duration >= self.config.release_window:
                    # Holding too long - immediately fail and turn off LED
                    led_index = self._get_current_led_index()
                    if led_index:
                        self.io_backend.set_led(led_index, False)
                        self.trial_events.append({'type': 'led_off', 'led': led_index, 'timestamp': self.get_current_time()})
                    self.end_trial(RESULT_HOLD_TOO_LONG, "Hold Too Long")
                    return
            
            # Check if wait period has ended
            if state_duration >= wait_duration:
                if self.current_press_time is None:
                    # No press within window
                    self.end_trial(RESULT_NO_PRESS, "No Press")
                # If button is pressed, continue waiting for release (handled above)
        
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
        if not self.session_started:
            return
        self.paused = not self.paused
    
    def toggle_mode(self) -> None:
        """Toggle between sequence3 and shaping1 modes"""
        self.config.mode = "shaping1" if self.config.mode == "sequence3" else "sequence3"
        # Reset session when mode changes
        if self.session_started:
            self.reset_session()
    
    def adjust_current_wait_time(self, delta: float) -> None:
        """Adjust wait time for current stage"""
        if self.state == TaskState.L1_WAIT:
            self.config.wait_L1 = max(0.1, min(10.0, self.config.wait_L1 + delta))
        elif self.state == TaskState.L2_WAIT:
            self.config.wait_L2 = max(0.1, min(10.0, self.config.wait_L2 + delta))
        elif self.state == TaskState.L3_WAIT:
            self.config.wait_L3 = max(0.1, min(10.0, self.config.wait_L3 + delta))
        elif self.state == TaskState.SHAPING_WAIT:
            if self.config.shaping_led == 1:
                self.config.wait_L1 = max(0.1, min(10.0, self.config.wait_L1 + delta))
            elif self.config.shaping_led == 2:
                self.config.wait_L2 = max(0.1, min(10.0, self.config.wait_L2 + delta))
            else:
                self.config.wait_L3 = max(0.1, min(10.0, self.config.wait_L3 + delta))
    
    def reset_session(self) -> None:
        """Reset session statistics"""
        self.trial_index = 0
        self.trial_results = []
        self.stats = {code: 0 for code in self.stats}
        self.adaptive_adjustments = []
        self.session_start_time = time.perf_counter()
        self.finished = False
        self.paused = False
        self.session_started = False
        self.enter_state(TaskState.ITI)

class UI:
    """User interface for the task"""
    
    def __init__(self, screen: pygame.Surface, config: Config):
        self.screen = screen
        self.config = config
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.show_help = False
        
        # Parameter input system
        self.input_mode = False
        self.active_input = None
        self.input_text = ""
        self.input_boxes = {}
        self._setup_input_boxes()
        
        # UI layout
        self.led_positions = [
            (80, 260),  # L1
            (160, 260),  # L2
            (240, 260)   # L3
        ]
        
        # Message display for feedback
        self.message_text = ""
        self.message_color = COLOR_WHITE
        self.message_timer = 0
        
        # Color constants for buttons
        self.BLUE = (0, 100, 200)
        self.ORANGE = (255, 165, 0)
    
    def _setup_input_boxes(self) -> None:
        """Setup parameter input boxes"""
        self.input_boxes = {
            'wait_L1': {'rect': pygame.Rect(500, 90, 70, 22), 'value': ''},
            'wait_L2': {'rect': pygame.Rect(500, 115, 70, 22), 'value': ''},
            'wait_L3': {'rect': pygame.Rect(500, 140, 70, 22), 'value': ''},
            'I1': {'rect': pygame.Rect(500, 165, 70, 22), 'value': ''},
            'I2': {'rect': pygame.Rect(500, 190, 70, 22), 'value': ''},
            'release_window': {'rect': pygame.Rect(500, 215, 70, 22), 'value': ''},
            'R_duration': {'rect': pygame.Rect(500, 240, 70, 22), 'value': ''},
            'ITI_fixed_correct': {'rect': pygame.Rect(800, 90, 70, 22), 'value': ''},
            'ITI_rand_correct': {'rect': pygame.Rect(800, 115, 70, 22), 'value': ''},
            'ITI_fixed_error': {'rect': pygame.Rect(800, 140, 70, 22), 'value': ''},
            'ITI_rand_error': {'rect': pygame.Rect(800, 165, 70, 22), 'value': ''},
            'max_trials': {'rect': pygame.Rect(800, 190, 70, 22), 'value': ''}
        }
    
    def handle_mouse_click(self, pos: tuple) -> None:
        """Handle mouse clicks on input boxes and buttons"""
        # Check save button
        save_button = pygame.Rect(400, 270, 80, 30)
        if save_button.collidepoint(pos):
            self.save_parameters()
            return
            
        # Check load button
        load_button = pygame.Rect(500, 270, 80, 30)
        if load_button.collidepoint(pos):
            self.load_parameters()
            return
        
        # Check apply button
        apply_button = pygame.Rect(600, 270, 120, 30)
        if apply_button.collidepoint(pos):
            # This will be handled in main loop
            return
        
        for param_name, box_info in self.input_boxes.items():
            if box_info['rect'].collidepoint(pos):
                self.input_mode = True
                self.active_input = param_name
                self.input_text = box_info['value']
                return
        
        # Click outside input boxes - deactivate input mode
        self.input_mode = False
        self.active_input = None
    
    def handle_text_input(self, text: str) -> None:
        """Handle text input for active input box"""
        if self.input_mode and self.active_input:
            self.input_text += text
            self.input_boxes[self.active_input]['value'] = self.input_text
    
    def handle_backspace(self) -> None:
        """Handle backspace in input box"""
        if self.input_mode and self.active_input and self.input_text:
            self.input_text = self.input_text[:-1]
            self.input_boxes[self.active_input]['value'] = self.input_text
    
    def apply_parameter_changes(self, config: Config) -> bool:
        """Apply parameter changes from input boxes to config"""
        try:
            for param_name, box_info in self.input_boxes.items():
                value_str = box_info['value'].strip()
                if value_str:  # Only update if there's a value
                    value = float(value_str)
                    if param_name == 'wait_L1':
                        config.wait_L1 = value
                    elif param_name == 'wait_L2':
                        config.wait_L2 = value
                    elif param_name == 'wait_L3':
                        config.wait_L3 = value
                    elif param_name == 'I1':
                        config.I1 = value
                    elif param_name == 'I2':
                        config.I2 = value
                    elif param_name == 'release_window':
                        config.release_window = value
                    elif param_name == 'R_duration':
                        config.R_duration = value
                    elif param_name == 'ITI_fixed_correct':
                        config.ITI_fixed_correct = value
                    elif param_name == 'ITI_rand_correct':
                        config.ITI_rand_correct = value
                    elif param_name == 'ITI_fixed_error':
                        config.ITI_fixed_error = value
                    elif param_name == 'ITI_rand_error':
                        config.ITI_rand_error = value
                    elif param_name == 'max_trials':
                        config.max_trials = int(value)
            return True
        except ValueError:
            return False
    
    def save_parameters(self) -> None:
        """Save current parameters to config.json"""
        try:
            # Get current parameter values from input boxes
            params = {}
            for param_name, box_info in self.input_boxes.items():
                value_str = box_info['value'].strip()
                if value_str:
                    if param_name == 'max_trials':
                        params[param_name] = int(value_str)
                    else:
                        params[param_name] = float(value_str)
            
            # Load existing config and update with new parameters
            try:
                with open('config.json', 'r') as f:
                    config_data = json.load(f)
            except FileNotFoundError:
                config_data = {}
            
            config_data.update(params)
            
            # Save to file
            with open('config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.show_message("参数保存成功!", COLOR_GREEN)
        except Exception as e:
            self.show_message(f"保存失败: {str(e)}", COLOR_RED)
    
    def load_parameters(self) -> None:
        """Load parameters from config.json"""
        try:
            with open('config.json', 'r') as f:
                config_data = json.load(f)
            
            # Update input boxes with loaded values
            for param_name in self.input_boxes.keys():
                if param_name in config_data:
                    self.input_boxes[param_name]['value'] = str(config_data[param_name])
            
            self.show_message("参数加载成功!", COLOR_GREEN)
        except FileNotFoundError:
            self.show_message("配置文件不存在!", COLOR_RED)
        except Exception as e:
            self.show_message(f"加载失败: {str(e)}", COLOR_RED)
    
    def show_message(self, text: str, color: tuple) -> None:
        """Show a temporary message"""
        self.message_text = text
        self.message_color = color
        self.message_timer = pygame.time.get_ticks() + 3000  # Show for 3 seconds
    
    def toggle_help(self) -> None:
        """Toggle help overlay"""
        self.show_help = not self.show_help
    
    def draw(self, state_machine: TaskStateMachine, io_backend: KeyboardScreenBackend) -> None:
        """Draw the UI"""
        self.screen.fill(COLOR_BLACK)
        
        if self.show_help:
            self._draw_help()
        else:
            self._draw_main_ui(state_machine, io_backend)
        
        pygame.display.flip()
    
    def _draw_main_ui(self, state_machine: TaskStateMachine, io_backend: KeyboardScreenBackend) -> None:
        """Draw main UI"""
        # Title
        title = self.font_large.render("Mouse Three-Key Sequence Task", True, COLOR_WHITE)
        self.screen.blit(title, (10, 10))
        
        # Session info
        y = 60
        info_lines = [
            f"Subject: {state_machine.config.subject_id}",
            f"Session: {state_machine.config.session_label}",
            f"Mode: {state_machine.config.mode.upper()}",
            f"Trial: {state_machine.trial_index}/{state_machine.config.max_trials}"
        ]
        
        for line in info_lines:
            text = self.font_medium.render(line, True, COLOR_WHITE)
            self.screen.blit(text, (10, y))
            y += 25
        
        # Current state
        y += 10
        state_text = f"State: {state_machine.state.value}"
        if state_machine.paused:
            state_text += " (PAUSED)"
        elif not state_machine.session_started:
            state_text += " (Press SPACE to start)"
        
        color = COLOR_YELLOW if state_machine.paused else COLOR_WHITE
        text = self.font_medium.render(state_text, True, color)
        self.screen.blit(text, (10, y))
        y += 25
        
        # Remaining time
        remaining_time = self._get_remaining_time(state_machine)
        time_text = f"Time: {remaining_time:.1f}s"
        text = self.font_medium.render(time_text, True, COLOR_WHITE)
        self.screen.blit(text, (10, y))
        
        # LEDs
        self._draw_leds(io_backend)
        
        # Reward indicator
        reward_color = COLOR_GREEN if io_backend.reward_active else COLOR_GRAY
        pygame.draw.circle(self.screen, reward_color, (320, 270), 20)
        reward_text = self.font_medium.render("REWARD", True, COLOR_WHITE)
        self.screen.blit(reward_text, (290, 310))
        
        # Statistics
        self._draw_statistics(state_machine)
        
        # Recent results
        self._draw_recent_results(state_machine)
        
        # Parameters
        self._draw_parameters(state_machine)
        
        # Controls
        self._draw_controls()
        
        # Error messages
        if state_machine.finished:
            finished_text = self.font_large.render("SESSION FINISHED", True, COLOR_RED)
            self.screen.blit(finished_text, (WIDTH//2 - 150, HEIGHT//2))
        
        # Display feedback messages
        if self.message_text and pygame.time.get_ticks() < self.message_timer:
            message_surface = self.font_medium.render(self.message_text, True, self.message_color)
            message_rect = message_surface.get_rect(center=(WIDTH//2, 50))
            # Draw background for better visibility
            bg_rect = message_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, COLOR_BLACK, bg_rect)
            pygame.draw.rect(self.screen, self.message_color, bg_rect, 2)
            self.screen.blit(message_surface, message_rect)
    
    def _draw_leds(self, io_backend: KeyboardScreenBackend) -> None:
        """Draw LED indicators"""
        for i, pos in enumerate(self.led_positions):
            color = COLOR_YELLOW if io_backend.led_states[i] else COLOR_GRAY
            pygame.draw.circle(self.screen, color, pos, self.config.led_radius)
            
            # LED labels
            label = self.font_medium.render(f"L{i+1}", True, COLOR_WHITE)
            label_rect = label.get_rect(center=(pos[0], pos[1] + 60))
            self.screen.blit(label, label_rect)
            
            # Button labels
            button_keys = [self.config.key_B1, self.config.key_B2, self.config.key_B3]
            button_label = self.font_small.render(f"({button_keys[i].upper()})", True, COLOR_WHITE)
            button_rect = button_label.get_rect(center=(pos[0], pos[1] + 80))
            self.screen.blit(button_label, button_rect)
    
    def _draw_statistics(self, state_machine: TaskStateMachine) -> None:
        """Draw statistics"""
        x, y = 10, 420
        
        stats_title = self.font_medium.render("STATISTICS", True, COLOR_WHITE)
        self.screen.blit(stats_title, (x, y))
        y += 30
        
        # Calculate total trials (excluding ITI errors)
        total_trials = sum(state_machine.stats.values())
        accuracy = (state_machine.stats[RESULT_CORRECT] / max(1, total_trials)) * 100
        
        stats_lines = [
            f"Total: {total_trials}",
            f"Correct: {state_machine.stats[RESULT_CORRECT]} ({accuracy:.1f}%)",
            f"No Press: {state_machine.stats[RESULT_NO_PRESS]}",
            f"Wrong Button: {state_machine.stats[RESULT_WRONG_BUTTON]}",
            f"Hold Too Long: {state_machine.stats[RESULT_HOLD_TOO_LONG]}",
            f"Premature: {state_machine.stats[RESULT_PREMATURE_PRESS]}",
            f"ITI Errors: {state_machine.iti_errors}"
        ]
        
        # Add ITI key details if any
        if state_machine.iti_key_counts:
            stats_lines.append("ITI Keys:")
            for key, count in sorted(state_machine.iti_key_counts.items()):
                stats_lines.append(f"  {key.upper()}: {count}")
        
        for line in stats_lines:
            text = self.font_small.render(line, True, COLOR_WHITE)
            self.screen.blit(text, (x, y))
            y += 20
    
    def _draw_recent_results(self, state_machine: TaskStateMachine) -> None:
        """Draw recent trial results"""
        x, y = 200, 400
        
        results_title = self.font_medium.render("RECENT RESULTS", True, COLOR_WHITE)
        self.screen.blit(results_title, (x, y))
        y += 30
        
        # Show last 320 results with expanded area (8 rows x 40 per row)
        recent_results = state_machine.trial_results[-320:]
        
        for i, result in enumerate(recent_results):
            color = RESULT_COLORS[result]
            rect_x = x + (i % 40) * 18  # 40 per row, smaller spacing
            rect_y = y + (i // 40) * 22  # 8 rows total, reduced vertical spacing
            
            pygame.draw.rect(self.screen, color, (rect_x, rect_y, 15, 18))
            
            # Draw result code
            code_text = self.font_small.render(str(result), True, COLOR_WHITE)
            code_rect = code_text.get_rect(center=(rect_x + 7, rect_y + 9))
            self.screen.blit(code_text, code_rect)
    
    def _draw_parameters(self, state_machine: TaskStateMachine) -> None:
        """Draw current parameters with input boxes"""
        params_text = self.font_medium.render("PARAMETERS", True, COLOR_WHITE)
        self.screen.blit(params_text, (400, 60))
        
        # Parameter labels and input boxes
        param_labels = [
            ("Wait L1:", 'wait_L1', state_machine.config.wait_L1),
            ("Wait L2:", 'wait_L2', state_machine.config.wait_L2),
            ("Wait L3:", 'wait_L3', state_machine.config.wait_L3),
            ("I1:", 'I1', state_machine.config.I1),
            ("I2:", 'I2', state_machine.config.I2),
            ("Release:", 'release_window', state_machine.config.release_window),
            ("Reward:", 'R_duration', state_machine.config.R_duration)
        ]
        
        for i, (label, param_name, current_value) in enumerate(param_labels):
            y_pos = 90 + i * 25
            
            # Draw label
            label_text = self.font_small.render(label, True, COLOR_WHITE)
            self.screen.blit(label_text, (400, y_pos + 3))
            
            # Draw input box
            box_info = self.input_boxes[param_name]
            box_color = COLOR_YELLOW if self.active_input == param_name else COLOR_WHITE
            pygame.draw.rect(self.screen, box_color, box_info['rect'], 2)
            
            # Draw current value or input text
            display_text = box_info['value'] if box_info['value'] else f"{current_value:.1f}"
            text_surface = self.font_small.render(display_text, True, COLOR_WHITE)
            text_rect = text_surface.get_rect()
            text_rect.centery = box_info['rect'].centery
            text_rect.x = box_info['rect'].x + 5
            self.screen.blit(text_surface, text_rect)
        
        # Second column for ITI parameters
        iti_labels = [
            ("ITI Fix Correct:", 'ITI_fixed_correct', state_machine.config.ITI_fixed_correct),
            ("ITI Rand Correct:", 'ITI_rand_correct', state_machine.config.ITI_rand_correct),
            ("ITI Fix Error:", 'ITI_fixed_error', state_machine.config.ITI_fixed_error),
            ("ITI Rand Error:", 'ITI_rand_error', state_machine.config.ITI_rand_error),
            ("Max Trials:", 'max_trials', state_machine.config.max_trials)
        ]
        
        for i, (label, param_name, current_value) in enumerate(iti_labels):
            y_pos = 90 + i * 25
            
            # Draw label
            label_text = self.font_small.render(label, True, COLOR_WHITE)
            self.screen.blit(label_text, (650, y_pos + 3))
            
            # Draw input box
            box_info = self.input_boxes[param_name]
            box_color = COLOR_YELLOW if self.active_input == param_name else COLOR_WHITE
            pygame.draw.rect(self.screen, box_color, box_info['rect'], 2)
            
            # Draw current value or input text
            if param_name == 'max_trials':
                display_text = box_info['value'] if box_info['value'] else str(int(current_value))
            else:
                display_text = box_info['value'] if box_info['value'] else f"{current_value:.1f}"
            text_surface = self.font_small.render(display_text, True, COLOR_WHITE)
            text_rect = text_surface.get_rect()
            text_rect.centery = box_info['rect'].centery
            text_rect.x = box_info['rect'].x + 5
            self.screen.blit(text_surface, text_rect)
        
        # Apply button - positioned in the center between two columns
        apply_button_rect = pygame.Rect(600, 270, 120, 30)
        apply_color = COLOR_GREEN if not self.input_mode else COLOR_GRAY
        pygame.draw.rect(self.screen, apply_color, apply_button_rect)
        apply_text = self.font_small.render("Apply Changes", True, COLOR_BLACK)
        apply_text_rect = apply_text.get_rect(center=apply_button_rect.center)
        self.screen.blit(apply_text, apply_text_rect)
        
        # Save button
        save_button_rect = pygame.Rect(400, 270, 80, 30)
        save_color = COLOR_BLUE if not self.input_mode else COLOR_GRAY
        pygame.draw.rect(self.screen, save_color, save_button_rect)
        save_text = self.font_small.render("Save", True, COLOR_WHITE)
        save_text_rect = save_text.get_rect(center=save_button_rect.center)
        self.screen.blit(save_text, save_text_rect)
        
        # Load button
        load_button_rect = pygame.Rect(500, 270, 80, 30)
        load_color = COLOR_ORANGE if not self.input_mode else COLOR_GRAY
        pygame.draw.rect(self.screen, load_color, load_button_rect)
        load_text = self.font_small.render("Load", True, COLOR_WHITE)
        load_text_rect = load_text.get_rect(center=load_button_rect.center)
        self.screen.blit(load_text, load_text_rect)
        
        # Store button rects for click detection
        self.apply_button_rect = apply_button_rect
        self.save_button_rect = save_button_rect
        self.load_button_rect = load_button_rect
    
    def _draw_controls(self) -> None:
        """Draw control instructions"""
        x, y = 10, 720
        
        controls_title = self.font_medium.render("CONTROLS", True, COLOR_WHITE)
        self.screen.blit(controls_title, (x, y))
        y += 25
        
        control_lines = [
            "SPACE: Start/Pause | R: Reset | Q: Quit | TAB: Mode | H: Help",
            "[/]: Adjust wait time | -/=: Adjust release window"
        ]
        
        for line in control_lines:
            text = self.font_small.render(line, True, COLOR_WHITE)
            self.screen.blit(text, (x, y))
            y += 18
    
    def _draw_help(self) -> None:
        """Draw help overlay"""
        # Semi-transparent background
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(COLOR_BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Help content
        x, y = 50, 50
        
        help_title = self.font_large.render("HELP - MOUSE SEQUENCE TASK", True, COLOR_WHITE)
        self.screen.blit(help_title, (x, y))
        y += 50
        
        help_lines = [
            "TASK MODES:",
            "  Sequence-3: Complete L1→I1→L2→I2→L3→Reward sequence",
            "  Shaping-1: Single LED press for immediate reward",
            "",
            "CONTROLS:",
            "  J, K, L: Task buttons (B1, B2, B3)",
            "  SPACE: Start session / Pause/Resume",
            "  R: Reset session statistics",
            "  TAB: Switch between Sequence-3 and Shaping-1 modes",
            "  H: Show/hide this help",
            "  Q: Quit program",
            "  [/]: Decrease/increase current wait time by 0.1s",
            "  -/=: Decrease/increase release window by 0.1s",
            "",
            "RELEASE LOGIC (CRITICAL):",
            "  1. Press correct button during LED wait period",
            "  2. Release within 'release window' after wait period ends",
            "  3. Example: 3s wait + 1s release window = 4s total to release",
            "",
            "RESULT CODES:",
            "  0 (Green): Correct completion",
            "  1 (Gray): No press within wait window",
            "  2 (Red): Wrong button pressed",
            "  3 (Orange): Held too long (past release deadline)",
            "  4 (Purple): Premature press (during ITI/intervals)",
            "",
            "Press H again to close help"
        ]
        
        for line in help_lines:
            if line.startswith("  "):
                text = self.font_small.render(line, True, COLOR_LIGHT_GRAY)
            elif line == "":
                y += 10
                continue
            elif line.endswith(":"):
                text = self.font_medium.render(line, True, COLOR_YELLOW)
            else:
                text = self.font_small.render(line, True, COLOR_WHITE)
            
            self.screen.blit(text, (x, y))
            y += 20
    
    def _get_remaining_time(self, state_machine: TaskStateMachine) -> float:
        """Get remaining time for current state"""
        state_duration = state_machine.get_state_duration()
        
        if state_machine.state == TaskState.ITI:
            return max(0, state_machine.iti_duration - state_duration)
        elif state_machine.state == TaskState.L1_WAIT:
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

def print_startup_info(config: Config, data_dir: str) -> None:
    """Print startup information"""
    print("=" * 60)
    print("MOUSE THREE-KEY SEQUENCE TASK")
    print("=" * 60)
    print(f"Subject ID: {config.subject_id}")
    print(f"Session: {config.session_label}")
    print(f"Mode: {config.mode}")
    print(f"Data directory: {data_dir}")
    print()
    print("HOTKEYS:")
    print("  SPACE: Start/Pause session")
    print("  R: Reset session")
    print("  Q: Quit")
    print("  TAB: Switch mode")
    print("  H: Help overlay")
    print("  [/]: Adjust wait time")
    print("  -/=: Adjust release window")
    print()
    print(f"Task buttons: {config.key_B1.upper()}, {config.key_B2.upper()}, {config.key_B3.upper()}")
    print("=" * 60)

def main():
    """Main program loop"""
    try:
        # Load configuration
        config = load_config()
        
        # Handle input method issues on Windows
        if sys.platform == "win32":
            # Disable IME for pygame
            disable_ime_for_pygame()
            print("Attempting to resolve input method issues...")
            
            # Try to set English keyboard layout
            if set_english_ime():
                print("Successfully switched to English input method")
            else:
                print("Warning: Could not automatically switch input method")
                print("If JKL keys don't work, please manually press Shift to switch to English input")
        
        # Initialize pygame
        screen = pygame.display.set_mode((config.window_width, config.window_height))
        pygame.display.set_caption("Mouse Three-Key Sequence Task")
        clock = pygame.time.Clock()
        
        # Initialize components
        io_backend = KeyboardScreenBackend(config)
        logger = TrialLogger(config)
        state_machine = TaskStateMachine(config, io_backend, logger)
        ui = UI(screen, config)
        
        # Print startup info
        print_startup_info(config, logger.data_dir)
        
        # Main loop
        running = True
        
        while running:
            # Process events
            events = io_backend.process_events()
            
            for event in events:
                if event['type'] == 'quit':
                    running = False
                elif event['type'] == 'keydown':
                    if event['key'] == 'q':
                        running = False
                    elif event['key'] == 'h':
                        ui.toggle_help()
                    elif event['key'] == 'backspace' and ui.input_mode:
                        ui.handle_backspace()
                    elif event['key'] == 'return' and ui.input_mode:
                        # Apply changes when Enter is pressed
                        if ui.apply_parameter_changes(config):
                            print("Parameters updated successfully")
                        else:
                            print("Error: Invalid parameter values")
                        ui.input_mode = False
                        ui.active_input = None
                    else:
                        state_machine.process_key_event(event)
                elif event['type'] == 'keyup':
                    state_machine.process_key_event(event)
                elif event['type'] == 'textinput':
                    ui.handle_text_input(event['text'])
                elif event['type'] == 'mousebuttondown':
                    if event['button'] == 1:  # Left click
                        mouse_pos = event['pos']
                        # Check if apply button was clicked
                        if hasattr(ui, 'apply_button_rect') and ui.apply_button_rect.collidepoint(mouse_pos):
                            if ui.apply_parameter_changes(config):
                                print("Parameters updated successfully")
                            else:
                                print("Error: Invalid parameter values")
                            ui.input_mode = False
                            ui.active_input = None
                        else:
                            ui.handle_mouse_click(mouse_pos)
            
            # Update state machine
            state_machine.update()
            
            # Draw UI
            ui.draw(state_machine, io_backend)
            
            # Control frame rate
            clock.tick(FPS)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        pygame.quit()
        print(f"\nSession ended. Data saved to: {logger.data_dir if 'logger' in locals() else 'N/A'}")
        print("Thank you for using the Mouse Sequence Task!")

if __name__ == "__main__":
    main()