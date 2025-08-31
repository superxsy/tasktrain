classdef (Abstract) IOBackend < handle
    % IOBackend IO后端抽象接口
    % 定义硬件控制和输入处理的统一接口
    
    methods (Abstract)
        % 硬件控制方法
        setLED(obj, ledIndex, state)        % 控制LED状态 (ledIndex: 1-3, state: true/false)
        buttonState = readButton(obj, buttonIndex)  % 读取按钮状态 (buttonIndex: 1-3, 返回: true/false)
        triggerReward(obj, duration)        % 触发奖励 (duration: 持续时间，秒)
        
        % 事件处理方法
        events = processEvents(obj)         % 处理输入事件，返回事件列表
        
        % 初始化和清理方法
        success = initialize(obj)           % 初始化硬件，返回成功状态
        cleanup(obj)                       % 清理资源
        
        % 状态查询方法
        connected = isConnected(obj)       % 检查连接状态
        info = getDeviceInfo(obj)          % 获取设备信息
    end
    
    methods
        function obj = IOBackend()
            % 基础构造函数
        end
        
        function success = testHardware(obj)
            % 硬件自检程序
            success = true;
            
            try
                fprintf('开始硬件自检...\n');
                
                % 测试LED
                fprintf('测试LED...');
                for i = 1:3
                    obj.setLED(i, true);
                    pause(0.2);
                    obj.setLED(i, false);
                    pause(0.1);
                end
                fprintf(' 完成\n');
                
                % 测试按钮
                fprintf('测试按钮状态读取...');
                for i = 1:3
                    state = obj.readButton(i);
                    fprintf(' B%d:%d', i, state);
                end
                fprintf(' 完成\n');
                
                % 测试奖励
                fprintf('测试奖励触发...');
                obj.triggerReward(0.1);
                fprintf(' 完成\n');
                
                fprintf('硬件自检完成\n');
                
            catch ME
                fprintf('硬件自检失败: %s\n', ME.message);
                success = false;
            end
        end
        
        function events = createButtonEvent(obj, eventType, buttonIndex)
            % 创建按钮事件
            event = struct();
            event.type = eventType;  % 'button_press' 或 'button_release'
            event.button = buttonIndex;
            event.timestamp = now;
            events = {event};
        end
        
        function logEvent(obj, message)
            % 记录事件日志
            timestamp = datestr(now, 'HH:MM:SS.FFF');
            fprintf('[%s] %s\n', timestamp, message);
        end
    end
end