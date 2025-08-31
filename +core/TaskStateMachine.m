classdef TaskStateMachine < handle
    % TaskStateMachine 任务状态机
    % 管理小鼠序列训练任务的状态转换和逻辑控制
    
    properties (Access = private)
        config              % 配置对象
        ioBackend          % IO后端接口
        logger             % 数据记录器
        
        % 状态相关
        currentState       % 当前状态
        stateStartTime     % 当前状态开始时间
        sessionStartTime   % 会话开始时间
        
        % 试次相关
        trialIndex         % 当前试次索引
        trialStartTime     % 当前试次开始时间
        trialEvents        % 当前试次事件列表
        stageTimestamps    % 阶段时间戳
        pressReleaseTimes  % 按压释放时间
        
        % 按键状态跟踪
        currentPressTime   % 当前按压开始时间
        currentPressButton % 当前按压的按钮
        lastButtonStates   % 上次按钮状态
        
        % 统计信息
        trialResults       % 试次结果历史
        itiErrorsCount     % ITI错误计数
        
        % 控制标志
        isRunning          % 是否正在运行
        isPaused           % 是否暂停
    end
    
    methods
        function obj = TaskStateMachine(config, ioBackend, logger)
            % 构造函数
            obj.config = config;
            obj.ioBackend = ioBackend;
            obj.logger = logger;
            
            obj.currentState = core.TaskState.ITI;
            obj.trialIndex = 0;
            obj.trialResults = [];
            obj.itiErrorsCount = 0;
            obj.isRunning = false;
            obj.isPaused = false;
            obj.lastButtonStates = [false, false, false];
            
            obj.resetTrial();
        end
        
        function startSession(obj)
            % 开始会话
            obj.sessionStartTime = tic;
            obj.isRunning = true;
            obj.isPaused = false;
            obj.startNewTrial();
            fprintf('会话开始\n');
        end
        
        function pauseSession(obj)
            % 暂停会话
            obj.isPaused = true;
            obj.enterState(core.TaskState.PAUSED);
            fprintf('会话暂停\n');
        end
        
        function resumeSession(obj)
            % 恢复会话
            obj.isPaused = false;
            obj.enterState(core.TaskState.ITI);
            fprintf('会话恢复\n');
        end
        
        function stopSession(obj)
            % 停止会话
            obj.isRunning = false;
            obj.enterState(core.TaskState.FINISHED);
            obj.ioBackend.setLED(1, false);
            obj.ioBackend.setLED(2, false);
            obj.ioBackend.setLED(3, false);
            fprintf('会话结束，共完成 %d 个试次\n', obj.trialIndex);
        end
        
        function update(obj, currentTime)
            % 主更新循环
            if ~obj.isRunning || obj.isPaused
                return;
            end
            
            % 处理输入事件
            events = obj.ioBackend.processEvents();
            for i = 1:length(events)
                obj.processEvent(events{i});
            end
            
            % 检查状态超时
            obj.checkStateTimeout();
            
            % 检查松开窗口
            obj.checkReleaseWindow();
            
            % 检查会话结束条件
            if obj.trialIndex >= obj.config.max_trials
                obj.stopSession();
            end
        end
        
        function enterState(obj, newState)
            % 进入新状态
            obj.currentState = newState;
            obj.stateStartTime = tic;
            
            % 记录状态转换事件
            obj.addEvent('state_enter', struct('state', char(core.TaskState.toString(newState))));
            
            % 执行状态特定的进入逻辑
            switch newState
                case core.TaskState.ITI
                    obj.enterITI();
                case core.TaskState.L1_WAIT
                    obj.enterL1Wait();
                case core.TaskState.I1
                    obj.enterI1();
                case core.TaskState.L2_WAIT
                    obj.enterL2Wait();
                case core.TaskState.I2
                    obj.enterI2();
                case core.TaskState.L3_WAIT
                    obj.enterL3Wait();
                case core.TaskState.REWARD
                    obj.enterReward();
                case core.TaskState.SHAPING_WAIT
                    obj.enterShapingWait();
            end
        end
        
        function enterITI(obj)
            % 进入ITI状态
            obj.ioBackend.setLED(1, false);
            obj.ioBackend.setLED(2, false);
            obj.ioBackend.setLED(3, false);
        end
        
        function enterL1Wait(obj)
            % 进入L1等待状态
            obj.ioBackend.setLED(1, true);
            obj.addEvent('led_on', struct('led', 1));
        end
        
        function enterI1(obj)
            % 进入I1间隔状态
            obj.ioBackend.setLED(1, false);
            obj.addEvent('led_off', struct('led', 1));
        end
        
        function enterL2Wait(obj)
            % 进入L2等待状态
            obj.ioBackend.setLED(2, true);
            obj.addEvent('led_on', struct('led', 2));
        end
        
        function enterI2(obj)
            % 进入I2间隔状态
            obj.ioBackend.setLED(2, false);
            obj.addEvent('led_off', struct('led', 2));
        end
        
        function enterL3Wait(obj)
            % 进入L3等待状态
            obj.ioBackend.setLED(3, true);
            obj.addEvent('led_on', struct('led', 3));
        end
        
        function enterReward(obj)
            % 进入奖励状态
            obj.ioBackend.setLED(3, false);
            obj.addEvent('led_off', struct('led', 3));
            obj.ioBackend.triggerReward(obj.config.R_duration);
            obj.addEvent('reward_trigger', struct('duration', obj.config.R_duration));
        end
        
        function enterShapingWait(obj)
            % 进入Shaping等待状态
            obj.ioBackend.setLED(obj.config.shaping_led, true);
            obj.addEvent('led_on', struct('led', obj.config.shaping_led));
        end
        
        function processEvent(obj, event)
            % 处理输入事件
            switch event.type
                case 'button_press'
                    obj.handleButtonPress(event.button);
                case 'button_release'
                    obj.handleButtonRelease(event.button);
            end
        end
        
        function handleButtonPress(obj, buttonIndex)
            % 处理按钮按下事件
            currentTime = toc(obj.sessionStartTime);
            
            % 记录事件
            obj.addEvent('button_press', struct('button', buttonIndex, 'timestamp', currentTime));
            
            % 根据当前状态处理按键
            switch obj.currentState
                case core.TaskState.ITI
                    % ITI期间按键为错误
                    obj.itiErrorsCount = obj.itiErrorsCount + 1;
                    obj.addEvent('iti_error', struct('button', buttonIndex));
                    
                case {core.TaskState.L1_WAIT, core.TaskState.L2_WAIT, core.TaskState.L3_WAIT, core.TaskState.SHAPING_WAIT}
                    % 等待状态下的按键处理
                    expectedButton = obj.getExpectedButton();
                    if buttonIndex == expectedButton
                        % 正确按键
                        obj.currentPressTime = tic;
                        obj.currentPressButton = buttonIndex;
                        obj.recordPressTime(buttonIndex, currentTime);
                    else
                        % 错误按键
                        obj.endTrial(2, 'Wrong Button');
                    end
                    
                case {core.TaskState.I1, core.TaskState.I2}
                    % 间隔期间按键为过早按压
                    obj.endTrial(4, 'Premature Press');
                    
                case core.TaskState.REWARD
                    % 奖励期间按键忽略
            end
        end
        
        function handleButtonRelease(obj, buttonIndex)
            % 处理按钮释放事件
            currentTime = toc(obj.sessionStartTime);
            
            % 记录事件
            obj.addEvent('button_release', struct('button', buttonIndex, 'timestamp', currentTime));
            
            % 如果是当前按压的按钮
            if buttonIndex == obj.currentPressButton && obj.currentPressTime > 0
                obj.recordReleaseTime(buttonIndex, currentTime);
                obj.currentPressTime = 0;
                obj.currentPressButton = 0;
                
                % 根据当前状态进行状态转换
                obj.handleSuccessfulRelease();
            end
        end
        
        function handleSuccessfulRelease(obj)
            % 处理成功的按键释放
            switch obj.currentState
                case core.TaskState.L1_WAIT
                    obj.enterState(core.TaskState.I1);
                case core.TaskState.L2_WAIT
                    obj.enterState(core.TaskState.I2);
                case core.TaskState.L3_WAIT
                    obj.enterState(core.TaskState.REWARD);
                case core.TaskState.SHAPING_WAIT
                    obj.enterState(core.TaskState.REWARD);
            end
        end
        
        function expectedButton = getExpectedButton(obj)
            % 获取当前状态期望的按钮
            switch obj.currentState
                case core.TaskState.L1_WAIT
                    expectedButton = 1;
                case core.TaskState.L2_WAIT
                    expectedButton = 2;
                case core.TaskState.L3_WAIT
                    expectedButton = 3;
                case core.TaskState.SHAPING_WAIT
                    expectedButton = obj.config.shaping_led;
                otherwise
                    expectedButton = 0;
            end
        end
        
        function checkStateTimeout(obj)
            % 检查状态超时
            stateDuration = toc(obj.stateStartTime);
            
            switch obj.currentState
                case core.TaskState.ITI
                    if stateDuration >= obj.getCurrentITIDuration()
                        obj.enterNextStateFromITI();
                    end
                    
                case core.TaskState.L1_WAIT
                    if stateDuration >= obj.config.wait_L1
                        obj.endTrial(1, 'No Press');
                    end
                    
                case core.TaskState.L2_WAIT
                    if stateDuration >= obj.config.wait_L2
                        obj.endTrial(1, 'No Press');
                    end
                    
                case core.TaskState.L3_WAIT
                    if stateDuration >= obj.config.wait_L3
                        obj.endTrial(1, 'No Press');
                    end
                    
                case core.TaskState.SHAPING_WAIT
                    waitTime = obj.config.(['wait_L' num2str(obj.config.shaping_led)]);
                    if stateDuration >= waitTime
                        obj.endTrial(1, 'No Press');
                    end
                    
                case core.TaskState.I1
                    if stateDuration >= obj.config.I1
                        obj.enterState(core.TaskState.L2_WAIT);
                    end
                    
                case core.TaskState.I2
                    if stateDuration >= obj.config.I2
                        obj.enterState(core.TaskState.L3_WAIT);
                    end
                    
                case core.TaskState.REWARD
                    if stateDuration >= obj.config.R_duration
                        obj.endTrial(0, 'Correct');
                    end
            end
        end
        
        function checkReleaseWindow(obj)
            % 检查松开窗口
            if obj.currentPressTime > 0
                pressDuration = toc(obj.currentPressTime);
                if pressDuration > obj.config.release_window
                    obj.endTrial(3, 'Hold Too Long');
                end
            end
        end
        
        function enterNextStateFromITI(obj)
            % 从ITI进入下一状态
            if strcmp(obj.config.mode, 'sequence3')
                obj.enterState(core.TaskState.L1_WAIT);
            else % shaping1
                obj.enterState(core.TaskState.SHAPING_WAIT);
            end
        end
        
        function duration = getCurrentITIDuration(obj)
            % 获取当前ITI持续时间
            if isempty(obj.trialResults) || obj.trialResults(end) == 0
                % 正确试次或第一个试次
                duration = obj.config.ITI_fixed_correct + rand() * obj.config.ITI_rand_correct;
            else
                % 错误试次
                duration = obj.config.ITI_fixed_error + rand() * obj.config.ITI_rand_error;
            end
        end
        
        function startNewTrial(obj)
            % 开始新试次
            obj.trialIndex = obj.trialIndex + 1;
            obj.trialStartTime = tic;
            obj.resetTrial();
            obj.enterState(core.TaskState.ITI);
            
            % 应用自适应调整
            if obj.config.adaptive_enabled
                obj.applyAdaptiveAdjustments();
            end
        end
        
        function endTrial(obj, resultCode, resultText)
            % 结束当前试次
            % 记录结果
            obj.trialResults(end+1) = resultCode;
            
            % 计算实际持续时间
            trialDuration = toc(obj.trialStartTime);
            itiDuration = toc(obj.stateStartTime);
            
            % 创建试次数据
            obj.logger.createTrialData(
                obj.config.mode, ...
                resultCode, ...
                resultText, ...
                obj.trialEvents, ...
                obj.stageTimestamps, ...
                obj.pressReleaseTimes, ...
                obj.config.R_duration, ...
                itiDuration, ...
                obj.itiErrorsCount
            );
            
            % 重置ITI错误计数
            obj.itiErrorsCount = 0;
            
            % 开始新试次
            obj.startNewTrial();
        end
        
        function resetTrial(obj)
            % 重置试次相关变量
            obj.trialEvents = {};
            obj.stageTimestamps = struct();
            obj.pressReleaseTimes = struct();
            obj.currentPressTime = 0;
            obj.currentPressButton = 0;
        end
        
        function addEvent(obj, eventType, eventData)
            % 添加事件到当前试次
            event = struct();
            event.type = eventType;
            event.timestamp = toc(obj.sessionStartTime);
            if nargin > 2
                fields = fieldnames(eventData);
                for i = 1:length(fields)
                    event.(fields{i}) = eventData.(fields{i});
                end
            end
            obj.trialEvents{end+1} = event;
        end
        
        function recordPressTime(obj, buttonIndex, timestamp)
            % 记录按压时间
            fieldName = sprintf('press_L%d_time', buttonIndex);
            obj.pressReleaseTimes.(fieldName) = timestamp;
        end
        
        function recordReleaseTime(obj, buttonIndex, timestamp)
            % 记录释放时间
            fieldName = sprintf('release_L%d_time', buttonIndex);
            obj.pressReleaseTimes.(fieldName) = timestamp;
        end
        
        function applyAdaptiveAdjustments(obj)
            % 应用自适应调整
            if length(obj.trialResults) < obj.config.adaptive_window
                return;
            end
            
            recentResults = obj.trialResults(end-obj.config.adaptive_window+1:end);
            correctCount = sum(recentResults == 0);
            accuracy = correctCount / length(recentResults);
            
            if accuracy >= obj.config.adaptive_threshold_high
                % 提高难度：缩短等待时间
                obj.adjustWaitTimes(-obj.config.adaptive_step);
            elseif accuracy <= obj.config.adaptive_threshold_low
                % 降低难度：延长等待时间
                obj.adjustWaitTimes(obj.config.adaptive_step);
            end
        end
        
        function adjustWaitTimes(obj, adjustment)
            % 调整等待时间
            waitParams = {'wait_L1', 'wait_L2', 'wait_L3'};
            for i = 1:length(waitParams)
                currentVal = obj.config.(waitParams{i});
                newVal = max(obj.config.min_wait, min(obj.config.max_wait, currentVal + adjustment));
                obj.config.(waitParams{i}) = newVal;
            end
        end
        
        % Getter方法
        function state = getCurrentState(obj)
            state = obj.currentState;
        end
        
        function duration = getStateDuration(obj)
            duration = toc(obj.stateStartTime);
        end
        
        function index = getTrialIndex(obj)
            index = obj.trialIndex;
        end
        
        function results = getTrialResults(obj)
            results = obj.trialResults;
        end
        
        function count = getITIErrorsCount(obj)
            count = obj.itiErrorsCount;
        end
        
        function running = isSessionRunning(obj)
            running = obj.isRunning;
        end
        
        function paused = isSessionPaused(obj)
            paused = obj.isPaused;
        end
    end
end