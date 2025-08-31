classdef TrialLogger < handle
    % TrialLogger 试次数据记录器
    % 负责记录实验数据到JSON和CSV文件
    
    properties (Access = private)
        config              % 配置对象
        dataDir            % 数据目录
        sessionDir         % 当前会话目录
        sessionFile        % 会话汇总CSV文件
        sessionStartTime   % 会话开始时间
        trialCount         % 试次计数
    end
    
    methods
        function obj = TrialLogger(config)
            % 构造函数
            obj.config = config;
            obj.trialCount = 0;
            obj.initializeSession();
        end
        
        function initializeSession(obj)
            % 初始化会话数据目录和文件
            try
                % 创建数据目录结构
                obj.dataDir = fullfile(pwd, 'data');
                if ~exist(obj.dataDir, 'dir')
                    mkdir(obj.dataDir);
                end
                
                subjectDir = fullfile(obj.dataDir, obj.config.subject_id);
                if ~exist(subjectDir, 'dir')
                    mkdir(subjectDir);
                end
                
                obj.sessionDir = fullfile(subjectDir, obj.config.session_label);
                if ~exist(obj.sessionDir, 'dir')
                    mkdir(obj.sessionDir);
                end
                
                % 创建会话汇总CSV文件
                obj.sessionFile = fullfile(obj.sessionDir, 'session_summary.csv');
                obj.initializeSessionCSV();
                
                % 记录会话开始时间
                obj.sessionStartTime = datetime('now');
                
                fprintf('数据记录初始化完成: %s\n', obj.sessionDir);
                
            catch ME
                error('数据记录初始化失败: %s', ME.message);
            end
        end
        
        function initializeSessionCSV(obj)
            % 初始化会话汇总CSV文件头
            headers = {
                'trial_index', 'mode', 'result_code', 'result_text', ...
                'trial_start_walltime_iso', 'trial_duration', ...
                'wait_L1', 'wait_L2', 'wait_L3', 'I1', 'I2', 'release_window', ...
                'press_L1_time', 'release_L1_time', 'press_L2_time', 'release_L2_time', ...
                'press_L3_time', 'release_L3_time', 'reward_duration_actual', ...
                'iti_duration_actual', 'iti_errors_count'
            };
            
            % 写入CSV头
            fid = fopen(obj.sessionFile, 'w');
            if fid == -1
                error('无法创建会话汇总文件: %s', obj.sessionFile);
            end
            
            fprintf(fid, '%s', strjoin(headers, ','));
            fprintf(fid, '\n');
            fclose(fid);
        end
        
        function logTrial(obj, trialData)
            % 记录单个试次数据
            obj.trialCount = obj.trialCount + 1;
            trialData.trial_index = obj.trialCount;
            
            % 保存JSON文件
            obj.saveTrialJSON(trialData);
            
            % 更新CSV文件
            obj.updateSessionCSV(trialData);
        end
        
        function saveTrialJSON(obj, trialData)
            % 保存试次数据到JSON文件
            try
                filename = sprintf('trial_%04d.json', trialData.trial_index);
                filepath = fullfile(obj.sessionDir, filename);
                
                % 添加配置快照
                trialData.config_snapshot = obj.config.getSnapshot();
                
                % 写入JSON文件
                json_str = jsonencode(trialData, 'PrettyPrint', true);
                fid = fopen(filepath, 'w');
                if fid == -1
                    error('无法创建试次文件: %s', filepath);
                end
                fprintf(fid, '%s', json_str);
                fclose(fid);
                
            catch ME
                warning('保存试次JSON失败: %s', ME.message);
            end
        end
        
        function updateSessionCSV(obj, trialData)
            % 更新会话汇总CSV文件
            try
                % 准备CSV行数据
                csvData = {
                    trialData.trial_index, ...
                    trialData.mode, ...
                    trialData.result_code, ...
                    trialData.result_text, ...
                    trialData.trial_start_walltime_iso, ...
                    trialData.trial_duration, ...
                    trialData.config_snapshot.wait_L1, ...
                    trialData.config_snapshot.wait_L2, ...
                    trialData.config_snapshot.wait_L3, ...
                    trialData.config_snapshot.I1, ...
                    trialData.config_snapshot.I2, ...
                    trialData.config_snapshot.release_window, ...
                    obj.getFieldValue(trialData, 'press_release_times.press_L1_time'), ...
                    obj.getFieldValue(trialData, 'press_release_times.release_L1_time'), ...
                    obj.getFieldValue(trialData, 'press_release_times.press_L2_time'), ...
                    obj.getFieldValue(trialData, 'press_release_times.release_L2_time'), ...
                    obj.getFieldValue(trialData, 'press_release_times.press_L3_time'), ...
                    obj.getFieldValue(trialData, 'press_release_times.release_L3_time'), ...
                    trialData.reward_duration_actual, ...
                    trialData.iti_duration_actual, ...
                    obj.getFieldValue(trialData, 'iti_errors_count')
                };
                
                % 写入CSV文件
                fid = fopen(obj.sessionFile, 'a');
                if fid == -1
                    error('无法打开会话汇总文件: %s', obj.sessionFile);
                end
                
                % 格式化数据
                formatStr = repmat('%s,', 1, length(csvData));
                formatStr = formatStr(1:end-1); % 移除最后的逗号
                formatStr = [formatStr '\n'];
                
                % 转换数据为字符串
                csvStrings = cell(size(csvData));
                for i = 1:length(csvData)
                    if isnumeric(csvData{i})
                        if isnan(csvData{i})
                            csvStrings{i} = '';
                        else
                            csvStrings{i} = num2str(csvData{i});
                        end
                    else
                        csvStrings{i} = char(csvData{i});
                    end
                end
                
                fprintf(fid, formatStr, csvStrings{:});
                fclose(fid);
                
            catch ME
                warning('更新会话CSV失败: %s', ME.message);
            end
        end
        
        function value = getFieldValue(obj, data, fieldPath)
            % 获取嵌套结构体字段值
            try
                parts = strsplit(fieldPath, '.');
                value = data;
                for i = 1:length(parts)
                    if isfield(value, parts{i})
                        value = value.(parts{i});
                    else
                        value = NaN;
                        return;
                    end
                end
            catch
                value = NaN;
            end
        end
        
        function createTrialData(obj, mode, resultCode, resultText, events, stageTimestamps, pressReleaseTimes, rewardDuration, itiDuration, itiErrorsCount)
            % 创建标准试次数据结构
            trialData = struct();
            
            % 基本信息
            trialData.subject_id = obj.config.subject_id;
            trialData.session_label = obj.config.session_label;
            trialData.mode = mode;
            
            % 时间信息
            trialData.trial_start_walltime_iso = char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ss.SSS''Z'''));
            trialData.trial_start_monotonic = 0.0; % 相对于会话开始的时间
            
            % 结果信息
            trialData.result_code = resultCode;
            trialData.result_text = resultText;
            
            % 事件和时间戳
            trialData.events = events;
            trialData.stage_timestamps = stageTimestamps;
            trialData.press_release_times = pressReleaseTimes;
            
            % 持续时间
            trialData.reward_duration_actual = rewardDuration;
            trialData.iti_duration_actual = itiDuration;
            trialData.iti_errors_count = itiErrorsCount;
            
            % 计算试次总时长
            if ~isempty(events) && length(events) >= 2
                trialData.trial_duration = events{end}.timestamp - events{1}.timestamp;
            else
                trialData.trial_duration = 0;
            end
            
            % 记录试次数据
            obj.logTrial(trialData);
        end
        
        function cleanup(obj)
            % 清理资源
            fprintf('数据记录器清理完成，共记录 %d 个试次\n', obj.trialCount);
        end
    end
end