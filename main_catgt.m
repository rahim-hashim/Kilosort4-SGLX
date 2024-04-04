kilosortFolder = 'C:\Users\Milner\OneDrive\Desktop\Kilosort-3';
addpath(genpath(kilosortFolder)) % path to kilosort folder
addpath('C:\Users\Milner\OneDrive\Desktop\Kilosort-3\npy-matlab-master') % for converting to Phy

%% set kilosort paths
pathToYourConfigFile = 'C:\Users\Milner\OneDrive\Desktop\Kilosort-3\configFiles'; % take from Github folder and put it somewhere else (together with the master_file)
% chanMapFile = 'neuropixPhase3A_kilosortChanMap.mat';
chanMapFile = 'neuropixels_NHP_channel_map_linear_v1.mat'; % NHP linear channel map

%% SET SESSION IDENTIFIERS 
% root = 'D:';
root = 'E:';
% set date
date = '20230126';      % YYYYMMDD
% set monkey
monkey = 'gandalf';     % lower case
% only perform catgt on ni
ni_only = 1;             % for extraction of square wave leading edges

%% SET KILOSORT PARAMETERS

% set specific probe
probes = [0,1,2,3];        % if empty, include all probes, or specify [0, 1..]

% set specific session
sessionNum = [];             % if empty, include all sessions [g0, g1..], or specify [0, 1,...]

% set destination folder
% dest_folder = "C:\\Users\\Milner\\SynologyDrive\\Rob\\%s_%s_%s";
dest_folder = pwd;

% CatGT prb field (only relevant with ni_only = 0 and runCatGT = 1)
cat_prb_fld = '0:3';          % see CatGT ReadMe for more details (default '0:3')

% delete CAT bin file after running CatGT to save space
deleteCATbin = 0; % 1=delete, 0 save (default 1)

%% find session directory

fprintf('Root Directory: %s\n', root);
rootFiles = dir(root);

% search for directory with <date>_<monkey>_<gN> format
pattern = 'g\d'; % all SpikeGLX directories and files end in gN
sessionFolders = {};
for i = 1:length(rootFiles)
    if ~rootFiles(i).isdir; continue; end
    folderName = rootFiles(i).name;
    if contains(folderName, monkey) && contains(folderName, date) && ~isempty(regexp(folderName, pattern, 'once'))
        sessionFolders = [sessionFolders, folderName];
    end
end

% no spikeglx output folder (i.e. gandalf_20240109_g0)
if isempty(sessionFolders); fprintf(['No SpikeGLX ' ...
        'session folder found for %s_%s\n'], monkey, date) ; return; end

% multiple spikeglx output folders (i.e. gandalf_20240109_g0, gandalf_20240109_g1)
if length(sessionFolders) > 1
    fprintf('Multiple sessions found\n')
    fprintf( '  %s ', sessionFolders{:} ); fprintf('\n')
    % run supercat (?)
end

%% Run CatGT / KS
for folder = 1:length(sessionFolders)
    sessionFolder = char(sessionFolders(folder));
    gNum = char(regexp(sessionFolder, pattern, 'match'));      % g0, g1...gN

    % directory found
    fprintf('Session Folder Found: %s\n', sessionFolder);
    if isempty(sessionNum)
        % all session included
    else
        sessionSpecified = cellfun(@(x)['g' num2str(x)], num2cell(sessionNum), 'UniformOutput', false);
        if ~any(strcmp(sessionSpecified, gNum))
            fprintf('  Session not specified in sessionNum field: %s\n', sessionFolder)
            continue
        end
    end

    sessionPath = fullfile(root, sessionFolder);
    imecDirs = dir(sessionPath);
    
    % dest folder
    destFolder = sprintf(dest_folder, monkey, date, gNum);  

    %% Run CatGT
    fprintf('Running CatGT on %s\n', sessionFolder);
    cd(fullfile(kilosortFolder, "CatGT-win/"));
    % catGTCommand = sprintf('runit.bat -dir=%s -run=%s_%s -prb_fld -dest=%s -g=%s -t=0  -prb=0:2 -ap -gblcar',...
    %                 root, monkey, date, root, gNum(2));
    if ni_only
        catGTCommand = sprintf('runit.bat -dir=%s -run=%s_%s -ni -g=%s -t=0',...
                    root, monkey, date, gNum(2));    
    else
        catGTCommand = sprintf('runit.bat -dir=%s -run=%s_%s -prb_fld -g=%s -t=0  -prb=%s -ap -gblcar',...
                        root, monkey, date, gNum(2), cat_prb_fld);
    end
    fprintf('  Bash command: %s\n', catGTCommand)
    system(catGTCommand);
    
    %% loop through all subdirectories and run kilosort
    for i = 1:length(imecDirs)
        pattern = 'imec\d';
        imecFolderName = imecDirs(i).name;
        imecNum = char(regexp(imecFolderName, pattern, 'match'));
        % not an imec directory
        if isempty(imecNum)
            continue
        end
        if isempty(probes)
            % all probes included
        else
            % only specified probe numbers
            imecSpecified = cellfun(@(x)['imec' num2str(x)], num2cell(probes), 'UniformOutput', false);
            if ~any(strcmp(imecSpecified, imecNum))
                fprintf('  Probe not specified in probe field: %s\n', imecFolderName)
                continue
            end
        end
    
        % data directory 
        rootZ = fullfile(sessionPath, imecFolderName);
        fprintf('Looking for data inside %s\n', rootZ)
           
        % temporary save directory (can set to same as data directory)
        rootH = fullfile(sessionPath, imecFolderName);
    
        % is there a channel map file in this folder?
        fs = dir(fullfile(rootZ, 'chan*.mat'));
        
        apPattern = '.ap';
        catPattern = 'cat';
        for j = 1:length(fs)

            % delete CatGT bin output after running
            if deleteCATbin == 1
                fprintf('\tDeleting CatGT output...\n');
                catgt_output = sprintf('%s_tcat.%s.ap.bin', sessionFolder, imecNum);
                catgt_path = fullfile(rootZ, catgt_output);
                if exist(catgt_path, "file")
                    delete(catgt_path);
                end
            end
        end
    end
end
%% 
