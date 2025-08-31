classdef Config < handle
    % Config 配置管理类
    % 管理小鼠序列训练任务的所有配置参数
    
    properties
        % 任务模式
        mode = 'sequence3'  % 'sequence3' | 'shaping1'
        shaping_led = 1     % Shaping模式使用的LED编号
        
        % 时序参数（秒）
        wait_L1 = 3.0       % L1等待时间
        wait_L2 = 3.0       % L2等待时间
        wait_L3 = 3.0       % L3等待时间
        I1 = 0.5            % L1和L2之间的间隔
        I2 = 0.5            % L2和L3之间的间隔
        R_duration = 0.3    % 奖励持续时间
        release_window = 1.0 % 松开窗口时间
        
        % ITI参数
        ITI_fixed_correct = 1.0   % 正确试次固定ITI
        ITI_rand_correct = 1.0    % 正确试次随机ITI
        ITI_fixed_error = 2.0     % 错误试次固定ITI
        ITI_rand_error = 1.0      % 错误试次随机ITI
        
        % 会话参数
        max_trials = 500          % 最大试次数
        subject_id = 'M001'       % 被试ID
        session_label = ''        % 会话标签
        
        % 自适应参数
        adaptive_enabled = false  % 是否启用自适应
        adaptive_window = 20      % 自适应评估窗口
        adaptive_threshold_high = 0.85  % 高阈值
        adaptive_threshold_low = 0.60   % 低阈值
        adaptive_step = 0.1       % 调整步长
        min_wait = 1.0           % 最小等待时间
        max_wait = 5.0           % 最大等待时间
        
        % 硬件参数
        arduino_port = ''         % Arduino端口
        led_pins = [22, 23, 24]   % LED引脚
        button_pins = [30, 31, 32] % 按钮引脚
        valve_pin = 26            % 电磁阀引脚
        debounce_time = 0.01      % 消抖时间
        
        % 键盘映射（模拟模式）
        key_L1 = 'j'             % L1对应键
        key_L2 = 'k'             % L2对应键
        key_L3 = 'l'             % L3对应键
        key_start_pause = ' '     % 开始/暂停键
        key_reset = 'r'          % 重置键
        key_mode_switch = char(9) % Tab键，模式切换
        key_help = 'h'           % 帮助键
    end
    
    methods
        function obj = Config()
            % 构造函数
            obj.generateSessionLabel();
        end
        
        function generateSessionLabel(obj)
            % 生成会话标签（基于当前时间）
            if isempty(obj.session_label)
                obj.session_label = datestr(now, 'yyyymmdd_HHMMSS');
            end
        end
        
        function success = loadFromFile(obj, filename)
            % 从JSON文件加载配置
            try
                if exist(filename, 'file')
                    data = jsondecode(fileread(filename));
                    fields = fieldnames(data);
                    for i = 1:length(fields)
                        if isprop(obj, fields{i})
                            obj.(fields{i}) = data.(fields{i});
                        end
                    end
                    success = true;
                else
                    warning('配置文件不存在: %s', filename);
                    success = false;
                end
            catch ME
                warning('加载配置文件失败: %s', ME.message);
                success = false;
            end
        end
        
        function success = saveToFile(obj, filename)
            % 保存配置到JSON文件
            try
                % 获取所有属性
                props = properties(obj);
                data = struct();
                for i = 1:length(props)
                    data.(props{i}) = obj.(props{i});
                end
                
                % 写入文件
                json_str = jsonencode(data, 'PrettyPrint', true);
                fid = fopen(filename, 'w');
                if fid == -1
                    error('无法创建文件: %s', filename);
                end
                fprintf(fid, '%s', json_str);
                fclose(fid);
                success = true;
            catch ME
                warning('保存配置文件失败: %s', ME.message);
                success = false;
            end
        end
        
        function valid = validate(obj)
            % 验证配置参数的合理性
            valid = true;
            
            % 检查时序参数
            if obj.wait_L1 <= 0 || obj.wait_L2 <= 0 || obj.wait_L3 <= 0
                warning('等待时间必须大于0');
                valid = false;
            end
            
            if obj.I1 <= 0 || obj.I2 <= 0
                warning('间隔时间必须大于0');
                valid = false;
            end
            
            if obj.release_window <= 0
                warning('松开窗口时间必须大于0');
                valid = false;
            end
            
            % 检查自适应参数
            if obj.adaptive_enabled
                if obj.adaptive_threshold_high <= obj.adaptive_threshold_low
                    warning('高阈值必须大于低阈值');
                    valid = false;
                end
                
                if obj.min_wait >= obj.max_wait
                    warning('最小等待时间必须小于最大等待时间');
                    valid = false;
                end
            end
            
            % 检查会话参数
            if obj.max_trials <= 0
                warning('最大试次数必须大于0');
                valid = false;
            end
            
            if isempty(obj.subject_id)
                warning('被试ID不能为空');
                valid = false;
            end
        end
        
        function snapshot = getSnapshot(obj)
            % 获取当前配置的快照（用于数据记录）
            props = properties(obj);
            snapshot = struct();
            for i = 1:length(props)
                snapshot.(props{i}) = obj.(props{i});
            end
        end
    end
end