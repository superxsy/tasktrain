classdef ArduinoBackend < io.IOBackend
    % ArduinoBackend Arduino硬件后端实现
    % 通过Arduino Due控制LED、读取按钮和触发奖励
    
    properties (Access = private)
        arduino            % Arduino对象
        config            % 配置对象
        
        % 引脚定义
        ledPins           % LED引脚数组 [L1, L2, L3]
        buttonPins        % 按钮引脚数组 [B1, B2, B3]
        valvePin          % 电磁阀引脚
        
        % 状态跟踪
        lastButtonStates  % 上次按钮状态
        debounceTimers    % 消抖计时器
        stableButtonStates % 稳定的按钮状态
        
        % 连接状态
        isConnected_      % 连接状态标志
        deviceInfo        % 设备信息
    end
    
    methods
        function obj = ArduinoBackend(config)
            % 构造函数
            obj@io.IOBackend();
            
            if nargin > 0
                obj.config = config;
            else
                % 使用默认配置
                obj.config = struct();
                obj.config.led_pins = [22, 23, 24];
                obj.config.button_pins = [30, 31, 32];
                obj.config.valve_pin = 26;
                obj.config.debounce_time = 0.01;
            end
            
            obj.ledPins = obj.config.led_pins;
            obj.buttonPins = obj.config.button_pins;
            obj.valvePin = obj.config.valve_pin;
            
            obj.lastButtonStates = [false, false, false];
            obj.debounceTimers = [0, 0, 0];
            obj.stableButtonStates = [false, false, false];
            obj.isConnected_ = false;
            
            % 尝试初始化
            obj.initialize();
        end
        
        function success = initialize(obj)
            % 初始化Arduino连接
            success = false;
            
            try
                fprintf('正在连接Arduino Due...\n');
                
                % 尝试自动检测Arduino端口
                if isempty(obj.config.arduino_port)
                    obj.config.arduino_port = obj.detectArduinoPort();
                end
                
                if isempty(obj.config.arduino_port)
                    warning('未找到Arduino设备');
                    return;
                end
                
                % 创建Arduino对象
                obj.arduino = arduino(obj.config.arduino_port, 'Due');
                
                % 配置引脚
                obj.configurePins();
                
                % 初始化状态
                obj.initializeState();
                
                obj.isConnected_ = true;
                obj.deviceInfo = struct('port', obj.config.arduino_port, 'board', 'Due');
                
                fprintf('Arduino连接成功: %s\n', obj.config.arduino_port);
                success = true;
                
            catch ME
                warning('Arduino初始化失败: %s', ME.message);
                obj.isConnected_ = false;
                success = false;
            end
        end
        
        function port = detectArduinoPort(obj)
            % 自动检测Arduino端口
            port = '';
            
            try
                % 获取可用串口列表
                ports = serialportlist;
                
                % 尝试连接每个端口
                for i = 1:length(ports)
                    try
                        testArduino = arduino(ports{i}, 'Due');
                        port = ports{i};
                        clear testArduino;
                        break;
                    catch
                        continue;
                    end
                end
                
            catch ME
                warning('端口检测失败: %s', ME.message);
            end
        end
        
        function configurePins(obj)
            % 配置Arduino引脚
            try
                % 配置LED引脚为输出
                for i = 1:length(obj.ledPins)
                    configurePin(obj.arduino, obj.ledPins(i), 'DigitalOutput');
                end
                
                % 配置按钮引脚为输入（带上拉电阻）
                for i = 1:length(obj.buttonPins)
                    configurePin(obj.arduino, obj.buttonPins(i), 'DigitalInput');
                    % Arduino Due内部上拉电阻需要通过代码设置
                end
                
                % 配置电磁阀引脚为输出
                configurePin(obj.arduino, obj.valvePin, 'DigitalOutput');
                
            catch ME
                error('引脚配置失败: %s', ME.message);
            end
        end
        
        function initializeState(obj)
            % 初始化硬件状态
            try
                % 关闭所有LED
                for i = 1:3
                    obj.setLED(i, false);
                end
                
                % 关闭电磁阀
                writeDigitalPin(obj.arduino, obj.valvePin, 0);
                
                % 读取初始按钮状态
                for i = 1:3
                    obj.stableButtonStates(i) = obj.readButton(i);
                    obj.lastButtonStates(i) = obj.stableButtonStates(i);
                end
                
            catch ME
                error('状态初始化失败: %s', ME.message);
            end
        end
        
        function setLED(obj, ledIndex, state)
            % 控制LED状态
            if ~obj.isConnected_
                return;
            end
            
            try
                if ledIndex >= 1 && ledIndex <= 3
                    writeDigitalPin(obj.arduino, obj.ledPins(ledIndex), state);
                    obj.logEvent(sprintf('LED%d %s', ledIndex, iif(state, 'ON', 'OFF')));
                end
            catch ME
                warning('LED控制失败: %s', ME.message);
            end
        end
        
        function buttonState = readButton(obj, buttonIndex)
            % 读取按钮状态（带消抖）
            buttonState = false;
            
            if ~obj.isConnected_ || buttonIndex < 1 || buttonIndex > 3
                return;
            end
            
            try
                % 读取原始状态（低电平有效）
                rawState = ~readDigitalPin(obj.arduino, obj.buttonPins(buttonIndex));
                
                % 消抖处理
                buttonState = obj.debounceButton(buttonIndex, rawState);
                
            catch ME
                warning('按钮读取失败: %s', ME.message);
            end
        end
        
        function debouncedState = debounceButton(obj, buttonIndex, currentState)
            % 按钮消抖算法
            currentTime = tic;
            
            if currentState ~= obj.lastButtonStates(buttonIndex)
                obj.debounceTimers(buttonIndex) = currentTime;
                obj.lastButtonStates(buttonIndex) = currentState;
            end
            
            if toc(obj.debounceTimers(buttonIndex)) > obj.config.debounce_time
                obj.stableButtonStates(buttonIndex) = currentState;
            end
            
            debouncedState = obj.stableButtonStates(buttonIndex);
        end
        
        function triggerReward(obj, duration)
            % 触发奖励（电磁阀）
            if ~obj.isConnected_
                return;
            end
            
            try
                % 打开电磁阀
                writeDigitalPin(obj.arduino, obj.valvePin, 1);
                obj.logEvent(sprintf('奖励触发: %.3fs', duration));
                
                % 使用定时器在指定时间后关闭
                t = timer('ExecutionMode', 'singleShot', ...
                         'StartDelay', duration, ...
                         'TimerFcn', @(~,~) obj.stopReward());
                start(t);
                
            catch ME
                warning('奖励触发失败: %s', ME.message);
            end
        end
        
        function stopReward(obj)
            % 停止奖励
            if obj.isConnected_
                try
                    writeDigitalPin(obj.arduino, obj.valvePin, 0);
                    obj.logEvent('奖励停止');
                catch ME
                    warning('奖励停止失败: %s', ME.message);
                end
            end
        end
        
        function events = processEvents(obj)
            % 处理输入事件
            events = {};
            
            if ~obj.isConnected_
                return;
            end
            
            try
                % 检查每个按钮的状态变化
                for i = 1:3
                    currentState = obj.readButton(i);
                    lastState = obj.stableButtonStates(i);
                    
                    if currentState && ~lastState
                        % 按钮按下
                        events{end+1} = obj.createButtonEvent('button_press', i);
                    elseif ~currentState && lastState
                        % 按钮释放
                        events{end+1} = obj.createButtonEvent('button_release', i);
                    end
                    
                    obj.stableButtonStates(i) = currentState;
                end
                
            catch ME
                warning('事件处理失败: %s', ME.message);
            end
        end
        
        function cleanup(obj)
            % 清理资源
            try
                if obj.isConnected_
                    % 关闭所有输出
                    for i = 1:3
                        obj.setLED(i, false);
                    end
                    obj.stopReward();
                    
                    % 清理Arduino对象
                    clear obj.arduino;
                    obj.isConnected_ = false;
                    
                    fprintf('Arduino连接已断开\n');
                end
            catch ME
                warning('Arduino清理失败: %s', ME.message);
            end
        end
        
        function connected = isConnected(obj)
            % 检查连接状态
            connected = obj.isConnected_;
            
            % 可以添加更详细的连接检查
            if connected
                try
                    % 尝试读取一个引脚状态来验证连接
                    readDigitalPin(obj.arduino, obj.buttonPins(1));
                catch
                    obj.isConnected_ = false;
                    connected = false;
                end
            end
        end
        
        function info = getDeviceInfo(obj)
            % 获取设备信息
            if obj.isConnected_
                info = obj.deviceInfo;
            else
                info = struct('status', 'disconnected');
            end
        end
        
        function reconnect(obj)
            % 重新连接
            obj.cleanup();
            pause(1);
            obj.initialize();
        end
    end
    
    methods (Access = private)
        function result = iif(obj, condition, trueValue, falseValue)
            % 内联if函数
            if condition
                result = trueValue;
            else
                result = falseValue;
            end
        end
    end
end