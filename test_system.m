function test_system()
    % TEST_SYSTEM 系统功能测试脚本
    % 
    % 用法:
    %   test_system()  - 运行所有测试
    %
    % 此脚本测试MATLAB移植版本的各个组件功能
    %
    % 作者: MATLAB移植版本
    % 日期: 2024
    
    fprintf('\n=== 小鼠序列训练任务系统测试 ===\n');
    fprintf('开始时间: %s\n', datestr(now));
    fprintf('======================================\n\n');
    
    % 测试计数器
    totalTests = 0;
    passedTests = 0;
    
    try
        % 添加项目路径
        projectRoot = fileparts(mfilename('fullpath'));
        addpath(genpath(projectRoot));
        
        % 测试1: 配置类
        fprintf('测试1: 配置管理类...\n');
        totalTests = totalTests + 1;
        if test_config_class()
            fprintf('  ✓ 配置类测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 配置类测试失败\n');
        end
        
        % 测试2: 任务状态枚举
        fprintf('\n测试2: 任务状态枚举...\n');
        totalTests = totalTests + 1;
        if test_task_state()
            fprintf('  ✓ 任务状态测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 任务状态测试失败\n');
        end
        
        % 测试3: 数据记录器
        fprintf('\n测试3: 数据记录器...\n');
        totalTests = totalTests + 1;
        if test_trial_logger()
            fprintf('  ✓ 数据记录器测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 数据记录器测试失败\n');
        end
        
        % 测试4: 模拟键盘后端
        fprintf('\n测试4: 模拟键盘后端...\n');
        totalTests = totalTests + 1;
        if test_sim_keyboard_backend()
            fprintf('  ✓ 模拟键盘后端测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 模拟键盘后端测试失败\n');
        end
        
        % 测试5: 状态机基本功能
        fprintf('\n测试5: 状态机基本功能...\n');
        totalTests = totalTests + 1;
        if test_state_machine_basic()
            fprintf('  ✓ 状态机基本功能测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 状态机基本功能测试失败\n');
        end
        
        % 测试6: 配置文件读写
        fprintf('\n测试6: 配置文件读写...\n');
        totalTests = totalTests + 1;
        if test_config_file_io()
            fprintf('  ✓ 配置文件读写测试通过\n');
            passedTests = passedTests + 1;
        else
            fprintf('  ✗ 配置文件读写测试失败\n');
        end
        
        % 显示测试结果
        fprintf('\n======================================\n');
        fprintf('测试完成时间: %s\n', datestr(now));
        fprintf('总测试数: %d\n', totalTests);
        fprintf('通过测试: %d\n', passedTests);
        fprintf('失败测试: %d\n', totalTests - passedTests);
        fprintf('成功率: %.1f%%\n', passedTests / totalTests * 100);
        
        if passedTests == totalTests
            fprintf('\n🎉 所有测试通过！系统准备就绪。\n');
        else
            fprintf('\n⚠️  部分测试失败，请检查相关组件。\n');
        end
        
    catch ME
        fprintf('\n❌ 测试过程中发生错误:\n');
        fprintf('错误信息: %s\n', ME.message);
        if ~isempty(ME.stack)
            fprintf('错误位置: %s (第 %d 行)\n', ME.stack(1).file, ME.stack(1).line);
        end
    end
    
    fprintf('======================================\n\n');
end

function success = test_config_class()
    % 测试配置类功能
    success = false;
    try
        % 创建配置对象
        config = core.Config();
        
        % 测试默认值
        assert(strcmp(config.subject_id, 'M001'), '默认被试ID错误');
        assert(strcmp(config.mode, 'sequence3'), '默认模式错误');
        assert(config.max_trials == 500, '默认最大试次数错误');
        
        % 测试参数修改
        config.subject_id = 'TEST';
        config.max_trials = 100;
        assert(strcmp(config.subject_id, 'TEST'), '参数修改失败');
        assert(config.max_trials == 100, '参数修改失败');
        
        % 测试验证功能
        assert(config.validate(), '配置验证失败');
        
        % 测试会话标签生成
        sessionLabel = config.generateSessionLabel();
        assert(~isempty(sessionLabel), '会话标签生成失败');
        
        success = true;
        
    catch ME
        fprintf('    配置类测试错误: %s\n', ME.message);
    end
end

function success = test_task_state()
    % 测试任务状态枚举
    success = false;
    try
        % 测试状态枚举
        states = enumeration('core.TaskState');
        assert(length(states) >= 8, '状态数量不足');
        
        % 测试状态转换为字符串
        stateStr = core.TaskState.toString(core.TaskState.ITI);
        assert(strcmp(stateStr, 'ITI'), '状态字符串转换错误');
        
        stateStr = core.TaskState.toString(core.TaskState.L1_WAIT);
        assert(strcmp(stateStr, 'L1_WAIT'), '状态字符串转换错误');
        
        success = true;
        
    catch ME
        fprintf('    任务状态测试错误: %s\n', ME.message);
    end
end

function success = test_trial_logger()
    % 测试数据记录器
    success = false;
    try
        % 创建临时配置
        config = core.Config();
        config.subject_id = 'TEST';
        
        % 创建记录器
        logger = core.TrialLogger(config);
        
        % 测试初始化
        logger.initializeSession();
        
        % 测试试次记录
        trialData = struct();
        trialData.trial_index = 1;
        trialData.timestamp = datestr(now, 'yyyy-mm-ddTHH:MM:SS');
        trialData.result_code = 0;
        trialData.reaction_time = 0.5;
        
        logger.logTrial(trialData);
        
        % 检查文件是否创建
        assert(exist(logger.sessionDir, 'dir') == 7, '会话目录未创建');
        
        success = true;
        
    catch ME
        fprintf('    数据记录器测试错误: %s\n', ME.message);
    end
end

function success = test_sim_keyboard_backend()
    % 测试模拟键盘后端
    success = false;
    try
        % 创建配置
        config = core.Config();
        
        % 创建模拟键盘后端
        backend = io.SimKeyboardBackend(config);
        
        % 测试初始化
        assert(backend.initialize(), '后端初始化失败');
        
        % 测试连接状态
        assert(backend.isConnected(), '连接状态错误');
        
        % 测试LED控制
        backend.setLED(1, true);
        backend.setLED(1, false);
        
        % 测试按钮状态读取
        buttonState = backend.readButton(1);
        assert(islogical(buttonState), '按钮状态类型错误');
        
        % 测试设备信息
        deviceInfo = backend.getDeviceInfo();
        assert(isstruct(deviceInfo), '设备信息格式错误');
        
        % 清理
        backend.cleanup();
        
        success = true;
        
    catch ME
        fprintf('    模拟键盘后端测试错误: %s\n', ME.message);
    end
end

function success = test_state_machine_basic()
    % 测试状态机基本功能
    success = false;
    try
        % 创建组件
        config = core.Config();
        config.subject_id = 'TEST';
        
        backend = io.SimKeyboardBackend(config);
        backend.initialize();
        
        logger = core.TrialLogger(config);
        
        % 创建状态机
        stateMachine = core.TaskStateMachine(config, backend, logger);
        
        % 测试初始状态
        currentState = stateMachine.getCurrentState();
        assert(currentState == core.TaskState.IDLE, '初始状态错误');
        
        % 测试会话控制
        assert(~stateMachine.isSessionRunning(), '会话状态错误');
        
        % 清理
        backend.cleanup();
        
        success = true;
        
    catch ME
        fprintf('    状态机基本功能测试错误: %s\n', ME.message);
    end
end

function success = test_config_file_io()
    % 测试配置文件读写
    success = false;
    try
        % 创建配置对象
        config = core.Config();
        config.subject_id = 'TEST_IO';
        config.max_trials = 123;
        
        % 保存到临时文件
        tempFile = 'test_config_temp.json';
        config.saveToFile(tempFile);
        
        % 检查文件是否存在
        assert(exist(tempFile, 'file') == 2, '配置文件未创建');
        
        % 创建新配置对象并加载
        config2 = core.Config();
        config2.loadFromFile(tempFile);
        
        % 验证加载的数据
        assert(strcmp(config2.subject_id, 'TEST_IO'), '配置加载失败');
        assert(config2.max_trials == 123, '配置加载失败');
        
        % 清理临时文件
        if exist(tempFile, 'file')
            delete(tempFile);
        end
        
        success = true;
        
    catch ME
        fprintf('    配置文件读写测试错误: %s\n', ME.message);
        
        % 清理临时文件
        tempFile = 'test_config_temp.json';
        if exist(tempFile, 'file')
            delete(tempFile);
        end
    end
end