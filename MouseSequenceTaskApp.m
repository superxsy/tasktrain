classdef MouseSequenceTaskApp < matlab.apps.AppBase
    % MouseSequenceTaskApp 小鼠序列训练任务主应用程序
    % MATLAB移植版本的三键序列小鼠训练任务
    
    properties (Access = private)
        % 核心组件
        config              % 配置管理器
        stateMachine        % 状态机
        ioBackend          % IO后端
        logger             % 数据记录器
        
        % 定时器
        updateTimer        % 主更新定时器
        
        % 应用状态
        isInitialized      % 初始化状态
        lastUpdateTime     % 上次更新时间
    end
    
    % 组件初始化
    methods (Access = private)
        
        function createComponents(app)
            % 创建UI组件（这里使用简化版本，实际可用App Designer）
            
            % 创建主窗口
            app.UIFigure = uifigure('Visible', 'off');
            app.UIFigure.Position = [100 100 800 600];
            app.UIFigure.Name = '小鼠序列训练任务 - MATLAB版';
            app.UIFigure.CloseRequestFcn = createCallbackFcn(app, @UIFigureCloseRequest, true);
            
            % 创建主面板
            app.MainPanel = uipanel(app.UIFigure);
            app.MainPanel.Position = [1 1 800 600];
            app.MainPanel.Title = '';
            
            % 会话信息面板
            app.SessionPanel = uipanel(app.MainPanel);
            app.SessionPanel.Position = [10 550 780 40];
            app.SessionPanel.Title = '会话信息';
            
            % 被试ID标签
            app.SubjectLabel = uilabel(app.SessionPanel);
            app.SubjectLabel.Position = [10 10 150 20];
            app.SubjectLabel.Text = '被试ID: M001';
            
            % 会话标签
            app.SessionLabelText = uilabel(app.SessionPanel);
            app.SessionLabelText.Position = [170 10 200 20];
            app.SessionLabelText.Text = '会话: 20240101_120000';
            
            % 模式标签
            app.ModeLabel = uilabel(app.SessionPanel);
            app.ModeLabel.Position = [380 10 150 20];
            app.ModeLabel.Text = '模式: Sequence-3';
            
            % 状态显示面板
            app.StatusPanel = uipanel(app.MainPanel);
            app.StatusPanel.Position = [10 450 780 90];
            app.StatusPanel.Title = '当前状态';
            
            % 状态文本
            app.StateLabel = uilabel(app.StatusPanel);
            app.StateLabel.Position = [10 40 200 30];
            app.StateLabel.Text = '状态: ITI';
            app.StateLabel.FontSize = 16;
            app.StateLabel.FontWeight = 'bold';
            
            % 倒计时标签
            app.CountdownLabel = uilabel(app.StatusPanel);
            app.CountdownLabel.Position = [220 40 150 30];
            app.CountdownLabel.Text = '倒计时: 0.0s';
            app.CountdownLabel.FontSize = 14;
            
            % 试次计数标签
            app.TrialLabel = uilabel(app.StatusPanel);
            app.TrialLabel.Position = [380 40 150 30];
            app.TrialLabel.Text = '试次: 0/500';
            app.TrialLabel.FontSize = 14;
            
            % LED指示器面板
            app.LEDPanel = uipanel(app.MainPanel);
            app.LEDPanel.Position = [10 350 780 90];
            app.LEDPanel.Title = 'LED指示器';
            
            % LED指示灯
            for i = 1:3
                app.(['LED' num2str(i) 'Lamp']) = uilamp(app.LEDPanel);
                app.(['LED' num2str(i) 'Lamp']).Position = [50 + (i-1)*150 30 30];
                app.(['LED' num2str(i) 'Lamp']).Color = [0.5 0.5 0.5];
                
                app.(['LED' num2str(i) 'Label']) = uilabel(app.LEDPanel);
                app.(['LED' num2str(i) 'Label']).Position = [40 + (i-1)*150 10 20];
                app.(['LED' num2str(i) 'Label']).Text = ['L' num2str(i)];
                app.(['LED' num2str(i) 'Label']).HorizontalAlignment = 'center';
            end
            
            % 奖励指示灯
            app.RewardLamp = uilamp(app.LEDPanel);
            app.RewardLamp.Position = [500 30 30];
            app.RewardLamp.Color = [0.5 0.5 0.5];
            
            app.RewardLabel = uilabel(app.LEDPanel);
            app.RewardLabel.Position = [490 10 50 20];
            app.RewardLabel.Text = 'Reward';
            app.RewardLabel.HorizontalAlignment = 'center';
            
            % 统计面板
            app.StatsPanel = uipanel(app.MainPanel);
            app.StatsPanel.Position = [10 200 780 140];
            app.StatsPanel.Title = '统计信息';
            
            % 统计标签
            app.TotalTrialsLabel = uilabel(app.StatsPanel);
            app.TotalTrialsLabel.Position = [10 100 150 20];
            app.TotalTrialsLabel.Text = '总试次: 0';
            
            app.CorrectRateLabel = uilabel(app.StatsPanel);
            app.CorrectRateLabel.Position = [170 100 150 20];
            app.CorrectRateLabel.Text = '正确率: 0.0%';
            
            app.ErrorsLabel = uilabel(app.StatsPanel);
            app.ErrorsLabel.Position = [330 100 150 20];
            app.ErrorsLabel.Text = '错误数: 0';
            
            app.ITIErrorsLabel = uilabel(app.StatsPanel);
            app.ITIErrorsLabel.Position = [490 100 150 20];
            app.ITIErrorsLabel.Text = 'ITI错误: 0';
            
            % 错误类型统计
            app.NoPressLabel = uilabel(app.StatsPanel);
            app.NoPressLabel.Position = [10 70 150 20];
            app.NoPressLabel.Text = '未按压: 0';
            
            app.WrongButtonLabel = uilabel(app.StatsPanel);
            app.WrongButtonLabel.Position = [170 70 150 20];
            app.WrongButtonLabel.Text = '按错按钮: 0';
            
            app.HoldTooLongLabel = uilabel(app.StatsPanel);
            app.HoldTooLongLabel.Position = [330 70 150 20];
            app.HoldTooLongLabel.Text = '按住过久: 0';
            
            app.PrematurePressLabel = uilabel(app.StatsPanel);
            app.PrematurePressLabel.Position = [490 70 150 20];
            app.PrematurePressLabel.Text = '过早按压: 0';
            
            % 结果条带（简化版）
            app.ResultsLabel = uilabel(app.StatsPanel);
            app.ResultsLabel.Position = [10 40 760 20];
            app.ResultsLabel.Text = '最近结果: ';
            
            % 控制按钮面板
            app.ControlPanel = uipanel(app.MainPanel);
            app.ControlPanel.Position = [10 50 780 140];
            app.ControlPanel.Title = '控制';
            
            % 控制按钮
            app.StartPauseButton = uibutton(app.ControlPanel, 'push');
            app.StartPauseButton.Position = [10 80 100 30];
            app.StartPauseButton.Text = '开始';
            app.StartPauseButton.ButtonPushedFcn = createCallbackFcn(app, @StartPauseButtonPushed, true);
            
            app.ResetButton = uibutton(app.ControlPanel, 'push');
            app.ResetButton.Position = [120 80 100 30];
            app.ResetButton.Text = '重置';
            app.ResetButton.ButtonPushedFcn = createCallbackFcn(app, @ResetButtonPushed, true);
            
            app.ModeSwitchButton = uibutton(app.ControlPanel, 'push');
            app.ModeSwitchButton.Position = [230 80 100 30];
            app.ModeSwitchButton.Text = '模式切换';
            app.ModeSwitchButton.ButtonPushedFcn = createCallbackFcn(app, @ModeSwitchButtonPushed, true);
            
            app.ConfigButton = uibutton(app.ControlPanel, 'push');
            app.ConfigButton.Position = [340 80 100 30];
            app.ConfigButton.Text = '配置';
            app.ConfigButton.ButtonPushedFcn = createCallbackFcn(app, @ConfigButtonPushed, true);
            
            app.HelpButton = uibutton(app.ControlPanel, 'push');
            app.HelpButton.Position = [450 80 100 30];
            app.HelpButton.Text = '帮助';
            app.HelpButton.ButtonPushedFcn = createCallbackFcn(app, @HelpButtonPushed, true);
            
            % 硬件选择
            app.HardwareLabel = uilabel(app.ControlPanel);
            app.HardwareLabel.Position = [10 40 80 20];
            app.HardwareLabel.Text = '硬件模式:';
            
            app.HardwareDropDown = uidropdown(app.ControlPanel);
            app.HardwareDropDown.Position = [100 40 150 20];
            app.HardwareDropDown.Items = {'模拟键盘', 'Arduino Due'};
            app.HardwareDropDown.Value = '模拟键盘';
            app.HardwareDropDown.ValueChangedFcn = createCallbackFcn(app, @HardwareDropDownValueChanged, true);
            
            % 连接状态
            app.ConnectionLabel = uilabel(app.ControlPanel);
            app.ConnectionLabel.Position = [260 40 200 20];
            app.ConnectionLabel.Text = '状态: 未连接';
            
            % 显示窗口
            app.UIFigure.Visible = 'on';
        end
    end
    
    % 回调函数
    methods (Access = private)
        
        function StartPauseButtonPushed(app, ~)
            % 开始/暂停按钮回调
            if ~app.stateMachine.isSessionRunning()
                app.startSession();
            elseif app.stateMachine.isSessionPaused()
                app.stateMachine.resumeSession();
                app.StartPauseButton.Text = '暂停';
            else
                app.stateMachine.pauseSession();
                app.StartPauseButton.Text = '继续';
            end
        end
        
        function ResetButtonPushed(app, ~)
            % 重置按钮回调
            app.resetSession();
        end
        
        function ModeSwitchButtonPushed(app, ~)
            % 模式切换按钮回调
            if strcmp(app.config.mode, 'sequence3')
                app.config.mode = 'shaping1';
                app.ModeLabel.Text = '模式: Shaping-1';
            else
                app.config.mode = 'sequence3';
                app.ModeLabel.Text = '模式: Sequence-3';
            end
        end
        
        function ConfigButtonPushed(app, ~)
            % 配置按钮回调
            app.openConfigDialog();
        end
        
        function HelpButtonPushed(app, ~)
            % 帮助按钮回调
            app.showHelp();
        end
        
        function HardwareDropDownValueChanged(app, ~)
            % 硬件模式切换回调
            app.switchHardwareMode();
        end
        
        function UIFigureCloseRequest(app, ~)
            % 窗口关闭回调
            app.cleanup();
            delete(app);
        end
    end
    
    % 应用程序方法
    methods (Access = private)
        
        function initializeApp(app)
            % 初始化应用程序
            try
                fprintf('初始化小鼠序列训练任务应用程序...\n');
                
                % 创建配置对象
                app.config = core.Config();
                
                % 加载配置文件
                configFile = 'config.json';
                if exist(configFile, 'file')
                    app.config.loadFromFile(configFile);
                end
                
                % 初始化IO后端
                app.initializeIOBackend();
                
                % 创建数据记录器
                app.logger = core.TrialLogger(app.config);
                
                % 创建状态机
                app.stateMachine = core.TaskStateMachine(app.config, app.ioBackend, app.logger);
                
                % 创建更新定时器
                app.updateTimer = timer('ExecutionMode', 'fixedRate', ...
                                      'Period', 0.01, ...
                                      'TimerFcn', @(~,~) app.updateApp());
                
                % 更新UI
                app.updateUI();
                
                app.isInitialized = true;
                fprintf('应用程序初始化完成\n');
                
            catch ME
                error('应用程序初始化失败: %s', ME.message);
            end
        end
        
        function initializeIOBackend(app)
            % 初始化IO后端
            if strcmp(app.HardwareDropDown.Value, 'Arduino Due')
                app.ioBackend = io.ArduinoBackend(app.config);
            else
                app.ioBackend = io.SimKeyboardBackend(app.config);
            end
            
            % 更新连接状态
            app.updateConnectionStatus();
        end
        
        function switchHardwareMode(app)
            % 切换硬件模式
            if app.stateMachine.isSessionRunning()
                uialert(app.UIFigure, '请先停止当前会话', '无法切换硬件');
                return;
            end
            
            % 清理当前后端
            if ~isempty(app.ioBackend)
                app.ioBackend.cleanup();
            end
            
            % 初始化新后端
            app.initializeIOBackend();
            
            % 更新状态机的IO后端
            app.stateMachine.ioBackend = app.ioBackend;
        end
        
        function updateConnectionStatus(app)
            % 更新连接状态显示
            if app.ioBackend.isConnected()
                info = app.ioBackend.getDeviceInfo();
                if isfield(info, 'type')
                    app.ConnectionLabel.Text = sprintf('状态: 已连接 (%s)', info.type);
                else
                    app.ConnectionLabel.Text = '状态: 已连接';
                end
                app.ConnectionLabel.FontColor = [0, 0.7, 0];
            else
                app.ConnectionLabel.Text = '状态: 未连接';
                app.ConnectionLabel.FontColor = [0.7, 0, 0];
            end
        end
        
        function startSession(app)
            % 开始会话
            if ~app.ioBackend.isConnected()
                uialert(app.UIFigure, '硬件未连接，无法开始会话', '连接错误');
                return;
            end
            
            % 验证配置
            if ~app.config.validate()
                uialert(app.UIFigure, '配置参数无效，请检查配置', '配置错误');
                return;
            end
            
            % 开始会话
            app.stateMachine.startSession();
            start(app.updateTimer);
            
            app.StartPauseButton.Text = '暂停';
        end
        
        function resetSession(app)
            % 重置会话
            if app.stateMachine.isSessionRunning()
                app.stateMachine.stopSession();
            end
            
            if isvalid(app.updateTimer)
                stop(app.updateTimer);
            end
            
            % 重新创建状态机
            app.stateMachine = core.TaskStateMachine(app.config, app.ioBackend, app.logger);
            
            app.StartPauseButton.Text = '开始';
            app.updateUI();
        end
        
        function updateApp(app)
            % 主更新循环
            if app.isInitialized && app.stateMachine.isSessionRunning()
                currentTime = now;
                app.stateMachine.update(currentTime);
                app.updateUI();
                app.lastUpdateTime = currentTime;
            end
        end
        
        function updateUI(app)
            % 更新用户界面
            try
                % 更新会话信息
                app.SubjectLabel.Text = sprintf('被试ID: %s', app.config.subject_id);
                app.SessionLabelText.Text = sprintf('会话: %s', app.config.session_label);
                
                if strcmp(app.config.mode, 'sequence3')
                    app.ModeLabel.Text = '模式: Sequence-3';
                else
                    app.ModeLabel.Text = '模式: Shaping-1';
                end
                
                % 更新状态信息
                currentState = app.stateMachine.getCurrentState();
                app.StateLabel.Text = sprintf('状态: %s', core.TaskState.toString(currentState));
                
                % 更新倒计时
                stateDuration = app.stateMachine.getStateDuration();
                app.CountdownLabel.Text = sprintf('倒计时: %.1fs', stateDuration);
                
                % 更新试次计数
                trialIndex = app.stateMachine.getTrialIndex();
                app.TrialLabel.Text = sprintf('试次: %d/%d', trialIndex, app.config.max_trials);
                
                % 更新LED指示器
                app.updateLEDIndicators();
                
                % 更新统计信息
                app.updateStatistics();
                
                % 更新连接状态
                app.updateConnectionStatus();
                
            catch ME
                % 忽略UI更新错误
            end
        end
        
        function updateLEDIndicators(app)
            % 更新LED指示器
            % 这里需要从IO后端获取LED状态
            % 简化版本，根据当前状态设置LED
            currentState = app.stateMachine.getCurrentState();
            
            % 重置所有LED
            for i = 1:3
                app.(['LED' num2str(i) 'Lamp']).Color = [0.5 0.5 0.5];
            end
            app.RewardLamp.Color = [0.5 0.5 0.5];
            
            % 根据状态设置LED
            switch currentState
                case core.TaskState.L1_WAIT
                    app.LED1Lamp.Color = [0 1 0];
                case core.TaskState.L2_WAIT
                    app.LED2Lamp.Color = [0 1 0];
                case core.TaskState.L3_WAIT
                    app.LED3Lamp.Color = [0 1 0];
                case core.TaskState.SHAPING_WAIT
                    ledIndex = app.config.shaping_led;
                    if ledIndex >= 1 && ledIndex <= 3
                        app.(['LED' num2str(ledIndex) 'Lamp']).Color = [0 1 0];
                    end
                case core.TaskState.REWARD
                    app.RewardLamp.Color = [1 1 0];
            end
        end
        
        function updateStatistics(app)
            % 更新统计信息
            results = app.stateMachine.getTrialResults();
            
            if ~isempty(results)
                totalTrials = length(results);
                correctTrials = sum(results == 0);
                correctRate = correctTrials / totalTrials * 100;
                
                % 错误类型统计
                noPressCount = sum(results == 1);
                wrongButtonCount = sum(results == 2);
                holdTooLongCount = sum(results == 3);
                prematurePressCount = sum(results == 4);
                
                % 更新标签
                app.TotalTrialsLabel.Text = sprintf('总试次: %d', totalTrials);
                app.CorrectRateLabel.Text = sprintf('正确率: %.1f%%', correctRate);
                app.ErrorsLabel.Text = sprintf('错误数: %d', totalTrials - correctTrials);
                
                app.NoPressLabel.Text = sprintf('未按压: %d', noPressCount);
                app.WrongButtonLabel.Text = sprintf('按错按钮: %d', wrongButtonCount);
                app.HoldTooLongLabel.Text = sprintf('按住过久: %d', holdTooLongCount);
                app.PrematurePressLabel.Text = sprintf('过早按压: %d', prematurePressCount);
            end
            
            % ITI错误
            itiErrors = app.stateMachine.getITIErrorsCount();
            app.ITIErrorsLabel.Text = sprintf('ITI错误: %d', itiErrors);
            
            % 最近结果（简化版）
            if ~isempty(results)
                recentResults = results(max(1, end-9):end);
                resultStr = '最近结果: ';
                for i = 1:length(recentResults)
                    resultStr = [resultStr sprintf('%d ', recentResults(i))];
                end
                app.ResultsLabel.Text = resultStr;
            end
        end
        
        function openConfigDialog(app)
            % 打开配置对话框（简化版）
            answer = inputdlg({
                '被试ID:', ...
                '最大试次数:', ...
                'L1等待时间(s):', ...
                'L2等待时间(s):', ...
                'L3等待时间(s):', ...
                '松开窗口(s):'
            }, '配置参数', 1, {
                app.config.subject_id, ...
                num2str(app.config.max_trials), ...
                num2str(app.config.wait_L1), ...
                num2str(app.config.wait_L2), ...
                num2str(app.config.wait_L3), ...
                num2str(app.config.release_window)
            });
            
            if ~isempty(answer)
                app.config.subject_id = answer{1};
                app.config.max_trials = str2double(answer{2});
                app.config.wait_L1 = str2double(answer{3});
                app.config.wait_L2 = str2double(answer{4});
                app.config.wait_L3 = str2double(answer{5});
                app.config.release_window = str2double(answer{6});
                
                % 保存配置
                app.config.saveToFile('config.json');
                
                % 更新UI
                app.updateUI();
            end
        end
        
        function showHelp(app)
            % 显示帮助信息
            helpText = {
                '小鼠序列训练任务 - MATLAB版', ...
                '', ...
                '操作说明:', ...
                '1. 选择硬件模式（模拟键盘或Arduino Due）', ...
                '2. 点击"开始"按钮开始实验', ...
                '3. 在模拟模式下，使用J/K/L键模拟按钮', ...
                '4. 点击"配置"可修改实验参数', ...
                '', ...
                '实验模式:', ...
                '- Sequence-3: 按顺序按压L1→L2→L3', ...
                '- Shaping-1: 只需按压指定LED对应的按钮', ...
                '', ...
                '错误类型:', ...
                '0 - 正确完成', ...
                '1 - 未按压（超时）', ...
                '2 - 按错按钮', ...
                '3 - 按住时间过长', ...
                '4 - 过早按压'
            };
            
            msgbox(helpText, '帮助', 'help');
        end
        
        function cleanup(app)
            % 清理资源
            try
                % 停止定时器
                if ~isempty(app.updateTimer) && isvalid(app.updateTimer)
                    stop(app.updateTimer);
                    delete(app.updateTimer);
                end
                
                % 停止会话
                if ~isempty(app.stateMachine) && app.stateMachine.isSessionRunning()
                    app.stateMachine.stopSession();
                end
                
                % 清理IO后端
                if ~isempty(app.ioBackend)
                    app.ioBackend.cleanup();
                end
                
                % 清理数据记录器
                if ~isempty(app.logger)
                    app.logger.cleanup();
                end
                
                fprintf('应用程序已清理\n');
                
            catch ME
                warning('应用程序清理失败: %s', ME.message);
            end
        end
    end
    
    % 应用程序启动和关闭
    methods (Access = public)
        
        function app = MouseSequenceTaskApp
            % 构造函数
            
            % 创建UI组件
            createComponents(app);
            
            % 初始化应用程序
            app.initializeApp();
            
            % 注册应用程序
            registerApp(app, app.UIFigure);
            
            if nargout == 0
                clear app
            end
        end
        
        function delete(app)
            % 析构函数
            app.cleanup();
            
            % 删除UI组件
            delete(app.UIFigure);
        end
    end
end