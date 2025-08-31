function run_task()
    % RUN_TASK 启动小鼠序列训练任务应用程序
    % 
    % 用法:
    %   run_task()  - 启动应用程序
    %
    % 示例:
    %   run_task();
    %
    % 作者: MATLAB移植版本
    % 日期: 2024
    
    try
        % 检查MATLAB版本
        if verLessThan('matlab', '9.4')
            error('此应用程序需要MATLAB R2018a或更高版本');
        end
        
        % 添加项目路径
        projectRoot = fileparts(mfilename('fullpath'));
        addpath(genpath(projectRoot));
        
        % 显示启动信息
        fprintf('\n=== 小鼠序列训练任务 - MATLAB版 ===\n');
        fprintf('版本: 1.0.0\n');
        fprintf('启动时间: %s\n', datestr(now));
        fprintf('项目路径: %s\n', projectRoot);
        fprintf('=====================================\n\n');
        
        % 检查必要的工具箱
        requiredToolboxes = {
            'Instrument Control Toolbox', ...
            'MATLAB Support Package for Arduino Hardware'
        };
        
        installedToolboxes = ver;
        toolboxNames = {installedToolboxes.Name};
        
        for i = 1:length(requiredToolboxes)
            if ~any(contains(toolboxNames, requiredToolboxes{i}))
                warning('推荐安装工具箱: %s', requiredToolboxes{i});
            end
        end
        
        % 检查配置文件
        configFile = fullfile(projectRoot, 'config.json');
        if ~exist(configFile, 'file')
            warning('配置文件不存在: %s', configFile);
            fprintf('将使用默认配置\n');
        else
            fprintf('加载配置文件: %s\n', configFile);
        end
        
        % 创建数据目录
        dataDir = fullfile(projectRoot, 'data');
        if ~exist(dataDir, 'dir')
            mkdir(dataDir);
            fprintf('创建数据目录: %s\n', dataDir);
        end
        
        % 启动应用程序
        fprintf('启动应用程序...\n\n');
        app = MouseSequenceTaskApp();
        
        % 显示使用提示
        fprintf('应用程序已启动！\n');
        fprintf('\n使用提示:\n');
        fprintf('- 在模拟模式下，使用 J/K/L 键模拟按钮\n');
        fprintf('- 使用空格键暂停/继续\n');
        fprintf('- 使用 R 键重置会话\n');
        fprintf('- 使用 M 键切换模式\n');
        fprintf('- 关闭窗口退出应用程序\n\n');
        
    catch ME
        fprintf('\n错误: 应用程序启动失败\n');
        fprintf('错误信息: %s\n', ME.message);
        fprintf('错误位置: %s (第 %d 行)\n', ME.stack(1).file, ME.stack(1).line);
        
        % 显示解决建议
        fprintf('\n解决建议:\n');
        fprintf('1. 确保MATLAB版本为R2018a或更高\n');
        fprintf('2. 检查所有必要文件是否存在\n');
        fprintf('3. 确保有足够的系统权限\n');
        fprintf('4. 检查配置文件格式是否正确\n\n');
        
        rethrow(ME);
    end
end