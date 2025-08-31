classdef TaskState < uint8
    % TaskState 任务状态枚举
    % 定义小鼠序列训练任务的所有可能状态
    
    enumeration
        ITI (1)           % 试次间间隔
        L1_WAIT (2)       % 等待L1按压
        I1 (3)            % L1和L2之间的间隔
        L2_WAIT (4)       % 等待L2按压
        I2 (5)            % L2和L3之间的间隔
        L3_WAIT (6)       % 等待L3按压
        REWARD (7)        % 奖励状态
        SHAPING_WAIT (8)  % Shaping模式等待
        PAUSED (9)        % 暂停状态
        FINISHED (10)     % 实验结束
    end
    
    methods (Static)
        function str = toString(state)
            % 将状态转换为字符串表示
            switch state
                case TaskState.ITI
                    str = 'ITI';
                case TaskState.L1_WAIT
                    str = 'L1_WAIT';
                case TaskState.I1
                    str = 'I1';
                case TaskState.L2_WAIT
                    str = 'L2_WAIT';
                case TaskState.I2
                    str = 'I2';
                case TaskState.L3_WAIT
                    str = 'L3_WAIT';
                case TaskState.REWARD
                    str = 'REWARD';
                case TaskState.SHAPING_WAIT
                    str = 'SHAPING_WAIT';
                case TaskState.PAUSED
                    str = 'PAUSED';
                case TaskState.FINISHED
                    str = 'FINISHED';
                otherwise
                    str = 'UNKNOWN';
            end
        end
    end
end