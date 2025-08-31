classdef SimKeyboardBackend < io.IOBackend
    % SimKeyboardBackend 模拟键盘后端实现
    % 使用键盘输入模拟硬件按钮，用于测试和演示
    
    properties (Access = private)
        config            % 配置对象
        
        % 状态跟踪
        keyStates         % 键盘状态映射
        ledStates         % LED状态模拟
        rewardActive      % 奖励状态
        
        % 事件队列
        eventQueue        % 待处理事件队列
        lastKeyStates     % 上次按键状态
        
        % 图形界面（可选）
        figHandle         % 图形窗口句柄
        ledIndicators     % LED指示器句柄
        buttonIndicators  % 按钮指示器句柄
        
        % 连接状态
        isConnected_      % 连接状态标志
        deviceInfo        % 设备信息
    end
    
    methods
        function obj = SimKeyboardBackend(config)
            % 构造函数
            obj@io.IOBackend();
            
            if nargin > 0
                obj.config = config;
            else
                % 使用默认配置
                obj.config = struct();
                obj.config.key_L1 = 'j';
                obj.config.key_L2 = 'k';
                obj.config.key_L3 = 'l';
            end
            
            obj.keyStates = containers.Map();
            obj.ledStates = [false, false, false];
            obj.rewardActive = false;
            obj.eventQueue = {};
            obj.lastKeyStates = [false, false, false];
            obj.isConnected_ = false;
            
            % 初始化
            obj.initialize();
        end
        
        function success = initialize(obj)
            % 初始化模拟后端
            success = true;
            
            try
                fprintf('初始化模拟键盘后端...\n');
                
                % 初始化按键映射
                obj.keyStates(obj.config.key_L1) = false;
                obj.keyStates(obj.config.key_L2) = false;
                obj.keyStates(obj.config.key_L3) = false;
                
                % 创建可视化界面
                obj.createVisualization();
                
                obj.isConnected_ = true;
                obj.deviceInfo = struct('type', 'Simulated', 'interface', 'Keyboard');
                
                fprintf('模拟后端初始化完成\n');
                fprintf('按键映射: L1=%s, L2=%s, L3=%s\n', ...
                    obj.config.key_L1, obj.config.key_L2, obj.config.key_L3);
                
            catch ME
                warning('模拟后端初始化失败: %s', ME.message);
                success = false;
            end
        end
        
        function createVisualization(obj)
            % 创建可视化界面
            try
                % 创建图形窗口
                obj.figHandle = figure('Name', '硬件模拟器', ...
                                     'NumberTitle', 'off', ...
                                     'Position', [100, 100, 400, 300], ...
                                     'KeyPressFcn', @obj.onKeyPress, ...
                                     'KeyReleaseFcn', @obj.onKeyRelease, ...
                                     'CloseRequestFcn', @obj.onFigureClose);
                
                % 设置焦点
                set(obj.figHandle, 'WindowStyle', 'normal');
                
                % 创建LED指示器
                obj.createLEDIndicators();
                
                % 创建按钮指示器
                obj.createButtonIndicators();
                
                % 添加说明文本
                obj.addInstructions();
                
            catch ME
                warning('可视化界面创建失败: %s', ME.message);
            end
        end
        
        function createLEDIndicators(obj)
            % 创建LED指示器
            obj.ledIndicators = [];
            
            for i = 1:3
                % LED圆圈
                x = 50 + (i-1) * 100;
                y = 200;
                
                obj.ledIndicators(i) = rectangle('Position', [x-20, y-20, 40, 40], ...
                                                'Curvature', [1, 1], ...
                                                'FaceColor', [0.3, 0.3, 0.3], ...
                                                'EdgeColor', 'black', ...
                                                'LineWidth', 2);
                
                % LED标签
                text(x, y-40, sprintf('LED%d', i), ...
                    'HorizontalAlignment', 'center', ...
                    'FontSize', 12, 'FontWeight', 'bold');
            end
        end
        
        function createButtonIndicators(obj)
            % 创建按钮指示器
            obj.buttonIndicators = [];
            keys = {obj.config.key_L1, obj.config.key_L2, obj.config.key_L3};
            
            for i = 1:3
                % 按钮矩形
                x = 50 + (i-1) * 100;
                y = 100;
                
                obj.buttonIndicators(i) = rectangle('Position', [x-25, y-15, 50, 30], ...
                                                   'Curvature', [0.2, 0.2], ...
                                                   'FaceColor', [0.8, 0.8, 0.8], ...
                                                   'EdgeColor', 'black', ...
                                                   'LineWidth', 2);
                
                % 按钮标签
                text(x, y, sprintf('B%d\n(%s)', i, upper(keys{i})), ...
                    'HorizontalAlignment', 'center', ...
                    'VerticalAlignment', 'middle', ...
                    'FontSize', 10, 'FontWeight', 'bold');
            end
        end
        
        function addInstructions(obj)
            % 添加操作说明
            instructions = {
                '硬件模拟器', ...
                '', ...
                sprintf('按键映射: %s=%s, %s=%s, %s=%s', ...
                    'L1', upper(obj.config.key_L1), ...
                    'L2', upper(obj.config.key_L2), ...
                    'L3', upper(obj.config.key_L3)), ...
                '', ...
                '绿色LED = 亮起', ...
                '灰色LED = 熄灭', ...
                '蓝色按钮 = 按下'
            };
            
            text(200, 50, instructions, ...
                'HorizontalAlignment', 'center', ...
                'VerticalAlignment', 'top', ...
                'FontSize', 9);
        end
        
        function onKeyPress(obj, ~, event)
            % 处理按键按下事件
            key = lower(event.Key);
            
            if obj.keyStates.isKey(key)
                if ~obj.keyStates(key)
                    obj.keyStates(key) = true;
                    buttonIndex = obj.getButtonIndex(key);
                    if buttonIndex > 0
                        obj.eventQueue{end+1} = obj.createButtonEvent('button_press', buttonIndex);
                        obj.updateButtonVisual(buttonIndex, true);
                        obj.logEvent(sprintf('按钮%d按下 (%s)', buttonIndex, upper(key)));
                    end
                end
            end
        end
        
        function onKeyRelease(obj, ~, event)
            % 处理按键释放事件
            key = lower(event.Key);
            
            if obj.keyStates.isKey(key)
                if obj.keyStates(key)
                    obj.keyStates(key) = false;
                    buttonIndex = obj.getButtonIndex(key);
                    if buttonIndex > 0
                        obj.eventQueue{end+1} = obj.createButtonEvent('button_release', buttonIndex);
                        obj.updateButtonVisual(buttonIndex, false);
                        obj.logEvent(sprintf('按钮%d释放 (%s)', buttonIndex, upper(key)));
                    end
                end
            end
        end
        
        function onFigureClose(obj, ~, ~)
            % 处理窗口关闭事件
            obj.cleanup();
        end
        
        function buttonIndex = getButtonIndex(obj, key)
            % 根据按键获取按钮索引
            if strcmp(key, obj.config.key_L1)
                buttonIndex = 1;
            elseif strcmp(key, obj.config.key_L2)
                buttonIndex = 2;
            elseif strcmp(key, obj.config.key_L3)
                buttonIndex = 3;
            else
                buttonIndex = 0;
            end
        end
        
        function setLED(obj, ledIndex, state)
            % 控制LED状态
            if ledIndex >= 1 && ledIndex <= 3
                obj.ledStates(ledIndex) = state;
                obj.updateLEDVisual(ledIndex, state);
                obj.logEvent(sprintf('LED%d %s', ledIndex, iif(state, 'ON', 'OFF')));
            end
        end
        
        function updateLEDVisual(obj, ledIndex, state)
            % 更新LED可视化
            if ~isempty(obj.ledIndicators) && ledIndex <= length(obj.ledIndicators)
                try
                    if state
                        set(obj.ledIndicators(ledIndex), 'FaceColor', [0, 1, 0]); % 绿色
                    else
                        set(obj.ledIndicators(ledIndex), 'FaceColor', [0.3, 0.3, 0.3]); % 灰色
                    end
                catch
                    % 忽略图形更新错误
                end
            end
        end
        
        function updateButtonVisual(obj, buttonIndex, pressed)
            % 更新按钮可视化
            if ~isempty(obj.buttonIndicators) && buttonIndex <= length(obj.buttonIndicators)
                try
                    if pressed
                        set(obj.buttonIndicators(buttonIndex), 'FaceColor', [0, 0.5, 1]); % 蓝色
                    else
                        set(obj.buttonIndicators(buttonIndex), 'FaceColor', [0.8, 0.8, 0.8]); % 灰色
                    end
                catch
                    % 忽略图形更新错误
                end
            end
        end
        
        function buttonState = readButton(obj, buttonIndex)
            % 读取按钮状态
            buttonState = false;
            
            if buttonIndex >= 1 && buttonIndex <= 3
                key = obj.getKeyForButton(buttonIndex);
                if obj.keyStates.isKey(key)
                    buttonState = obj.keyStates(key);
                end
            end
        end
        
        function key = getKeyForButton(obj, buttonIndex)
            % 根据按钮索引获取对应按键
            switch buttonIndex
                case 1
                    key = obj.config.key_L1;
                case 2
                    key = obj.config.key_L2;
                case 3
                    key = obj.config.key_L3;
                otherwise
                    key = '';
            end
        end
        
        function triggerReward(obj, duration)
            % 触发奖励
            obj.rewardActive = true;
            obj.logEvent(sprintf('奖励触发: %.3fs', duration));
            
            % 使用定时器模拟奖励持续时间
            t = timer('ExecutionMode', 'singleShot', ...
                     'StartDelay', duration, ...
                     'TimerFcn', @(~,~) obj.stopReward());
            start(t);
        end
        
        function stopReward(obj)
            % 停止奖励
            obj.rewardActive = false;
            obj.logEvent('奖励停止');
        end
        
        function events = processEvents(obj)
            % 处理输入事件
            events = obj.eventQueue;
            obj.eventQueue = {}; % 清空事件队列
        end
        
        function cleanup(obj)
            % 清理资源
            try
                if ~isempty(obj.figHandle) && isvalid(obj.figHandle)
                    delete(obj.figHandle);
                end
                obj.isConnected_ = false;
                fprintf('模拟后端已清理\n');
            catch ME
                warning('模拟后端清理失败: %s', ME.message);
            end
        end
        
        function connected = isConnected(obj)
            % 检查连接状态
            connected = obj.isConnected_ && ...
                       (~isempty(obj.figHandle) && isvalid(obj.figHandle));
        end
        
        function info = getDeviceInfo(obj)
            % 获取设备信息
            if obj.isConnected_
                info = obj.deviceInfo;
                info.led_states = obj.ledStates;
                info.reward_active = obj.rewardActive;
            else
                info = struct('status', 'disconnected');
            end
        end
        
        function focusWindow(obj)
            % 将焦点设置到模拟器窗口
            if ~isempty(obj.figHandle) && isvalid(obj.figHandle)
                figure(obj.figHandle);
            end
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