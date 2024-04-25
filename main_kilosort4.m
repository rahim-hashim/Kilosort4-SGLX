%% RH UPDATED 
% 12/13/2023 - loops to run multiple .bin files at once (RH)
% 12/15/2023 - specify specific probes (RH)
% 12/20/2023 - run CatGT and incorporate output in kilosort
% 12/26/2023 - flags for specifying input (CatGT vs. raw) and destination
% 1/12/2024  - delete temp and cat_bin file after running KS to save space
% 1/22/2024  - added extract_waveform.bat functionality to generate
% waveform and templateview before deleting temp.wh
% 1/23/2024  - updated data_shift, trackAndSort and make_fig to save KS output figures
% 1/28/2024  - added TPrime
% 2/14/2024  - write adjusted .npy spiketimes to ks folder
% 3/13/2024  - included kilosort4 pipieline

% kilosortFolder = 'C:\Users\Milner\OneDrive\Desktop\Kilosort-3';
kilosortFolder = 'C:\Users\Penfield\Documents\GitHub\Kilosort4-SGLX';
addpath(genpath(kilosortFolder)) % path to kilosort folder

% baseFolder = 'C:\Users\Milner\OneDrive\Desktop\Kilosort-3';
baseFolder = 'C:\Users\Penfield\Documents\GitHub\Kilosort4-SGLX';
addpath([baseFolder '\npy-matlab-master']) % for converting to Phy

%% set kilosort paths
% pathToYourConfigFile = 'C:\Users\Milner\OneDrive\Desktop\Kilosort-3\configFiles'; % take from Github folder and put it somewhere else (together with the master_file)
pathToYourConfigFile = [baseFolder '\configFiles'];
% chanMapFile = 'neuropixPhase3A_kilosortChanMap.mat';
chanMapFile = 'neuropixels_NHP_channel_map_linear_v1.mat'; % NHP linear channel map

%% SET SESSION IDENTIFIERS 
% root = 'D:';
% root = 'C:\Users\Milner\SynologyDrive\Rob\gandalf_20231223';
root = 'C:\Users\Penfield\Downloads\';
% root = 'C:\SGL_DATA\';
% set date
date = '20240115';      % YYYYMMDD
% set monkey
monkey = 'gandalf';     % lower case

%% SET KILOSORT PARAMETERS

% set specific probe
probes = [];        % if empty, include all probes, or specify [0, 1..]

% set specific session
sessionNum = [0];             % if empty, include all sessions [g0, g1..], or specify

% set destination folder
dest_folder = "C:\\Users\\Milner\\SynologyDrive\\Rob\\%s_%s_%s";

% run Kilosort
runKilosort4 = 1; %1=run, 0=don't run (default 1)

% run CatGT
runCatGT = 1;  % 1=run, 0=don't run (default 1)

% CatGT prb field (only relevant with runCatGT = 1)
cat_prb_fld = '0:2';          % see CatGT ReadMe for more details (default '0:3')

% perform Kilosort on CatGT output
includeCatGT = 2; % 0=do not include, 1=both non-CatGT+CatGT, 2=only CatGT (default 2)

% perform phy extract-waveforms
extract_waveforms = 1; % 1=run extract-waveforms, 0=dont run extract-waveforms

% delete CAT bin file after running CatGT to save space
deleteCATbin = 0; % 1=delete, 0 save (default 1)

% delete temp_wh.dat after running KS to save space
deleteTemp = 0;   % 1=delete, 0=save (default 1)

% run TPrime
runTPrime = 1;    % 1=run, 0=dont run (default 1) 

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
    % keep only directories and get rid of '.' and '..'
    imecDirs = imecDirs([imecDirs.isdir]);
    imecDirs = imecDirs(~ismember({imecDirs.name}, {'.', '..'}));
    % for TPrime
    tprime_struct = struct(...
        'nidq_tcat', '',...
        'imec_tcat_list', [],...
        'sample_rates', [],...
        'spiketime_sec_files', [],...
        'spiketime_sec_adj_files', []...
    );
    
    % dest folder
    destFolder = sprintf(dest_folder, monkey, date, gNum);  

    %% Run CatGT
    ni_tcat = '';
    if runCatGT == 1
        fprintf('Running CatGT on %s\n', sessionFolder);
        cd(fullfile(kilosortFolder, "CatGT-win/"));
        catGTCommand = sprintf('runit.bat -dir=%s -run=%s_%s -prb_fld -g=%s -t=0 -ni -prb=%s -ap -gblcar',...
                        root, monkey, date, gNum(2), cat_prb_fld);
        fprintf('  Bash command: %s\n', catGTCommand)
%         system(catGTCommand);
    else
        fprintf('Not running CatGT\n');
    end
    % find name of tcat.nidq.xd with .txt extension
    tprime_struct.nidq_tcat = dir(fullfile(sessionPath, '*tcat.nidq.xd*.txt'));
    if isempty(tprime_struct.nidq_tcat)
        fprintf('   WARNING: Missing tcat.nidq.xd file. TPrime will not run.\n')
        runTPrime = 0;
    end
    
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
                fprintf('Skipping Probe not specified in probe field: %s\n', imecFolderName)
                continue
            end
        end
    
        % data directory 
        rootZ = fullfile(sessionPath, imecFolderName);
        fprintf('Looking for data inside %s\n', rootZ)
           
        % temporary save directory (can set to same as data directory)
        rootH = fullfile(sessionPath, imecFolderName);
    
        % run kilosort
        ops.trange    = [0 Inf]; % time range to sort
        ops.NchanTOT  = 385; % total number of channels in your recording
        
        run(fullfile(pathToYourConfigFile, 'configFile384.m'))
        ops.chanMap = fullfile(pathToYourConfigFile, chanMapFile);
    
        % this block runs all the steps of the algorithm
        % main parameter changes from Kilosort2 to v2.5
        ops.sig        = 20;  % spatial smoothness constant for registration
        ops.fshigh     = 300; % high-pass more aggresively
        ops.nblocks    = 5; % blocks for registration. 0 turns it off, 1 does rigid registration. Replaces "datashift" option. 
        
        % main parameter changes from Kilosort2.5 to v3.0
        ops.Th       = [9 9];
        % is there a channel map file in this folder?
        fs = dir(fullfile(rootZ, 'chan*.mat'));
        if ~isempty(fs)
            ops.chanMap = fullfile(rootZ, fs(1).name);
            fprintf('\tNo channel map found...\n')
        else
            fprintf('\tChannel map: %s\n', ops.chanMap)
        end
        
        % find the binary file
        fs          = [dir(fullfile(rootZ, '*.bin'))];
        if isempty(fs); fprintf('\tNo binary files found...\n'); continue; end
        
        apPattern = '.ap';
        catPattern = 'cat';
        for j = 1:length(fs)
            fileName = fs(j).name;
            ops.fproc   = fullfile(rootH, 'temp_wh.dat'); % proc file on a fast SSD
    
            % only perform kilosort on .ap files (skip lf.bin files)
            apMatch = regexp(fileName, apPattern, 'match', 'once');
            if isempty(apMatch); continue; end
    
            ops.fbinary = fullfile(rootZ, fileName);
            fprintf('\tBinary file found: %s \n', fileName)
            fprintf('\t  Reading meta file...\n')
            metaFile = SGLX_readMeta.ReadMeta(fileName, rootZ);
            sample_rate = str2double(metaFile.imSampRate);
            fprintf('\t\t Sampling rate: %.2f\n', sample_rate)
    
            % perform on CatGT output as well?
            catMatch = regexp(fileName, catPattern, 'match', 'once');
            if includeCatGT==0 && ~isempty(catMatch); fprintf('\t  Skipping: %s (missing CAT file)\n', fileName); continue; end % skip if CatGT
            if includeCatGT==2 && isempty(catMatch); fprintf('\t  Skipping: %s (missing CAT file)\n', fileName); continue; end % skip if not CatGT
            if ~isempty(catMatch); finalDestFolder=fullfile(rootH, [imecFolderName '_ks_cat']); ops.fproc = fullfile(rootH, 'temp_wh_cat.dat'); % proc file on a fast SSD
            else; finalDestFolder=fullfile(rootH, [imecFolderName '_ks_cat']);
            end
            
            % make directory for all ks output
            if ~exist(finalDestFolder, "dir")
                mkdir(finalDestFolder)
            end

            % make directory for ks output figures
            figPath = fullfile(rootH, 'KS_figures');
            if ~exist(figPath, 'dir')
                mkdir(figPath);
            end
            
            % run Kilosort
            if runKilosort4
                tic;
                fprintf('\tRunning Kilosort4...\n');
                cd(fullfile(kilosortFolder, "kilosort4-win/"));
                % run kilosort4 from python
                %  arg 1 = imec data dir
                %  arg 2 = number of channels
                %  arg 3 = channel map file path
                kilo4Command = sprintf('runit.bat %s %d %s',...
                                ops.fbinary, ops.NchanTOT, ops.chanMap);
                fprintf('\t\tBash command: %s\n', kilo4Command)
                system(kilo4Command);
                % save to destination folder
                fprintf('\tKilosort4 complete in %d sec.\n', toc);
            end
            fprintf('\tDestination Folder: %s \n', finalDestFolder)
    
            % delete CatGT bin output after running
            if deleteCATbin == 1
                fprintf('\tDeleting CatGT output...\n');
                catgt_output = sprintf('%s_tcat.%s.ap.bin', sessionFolder, imecNum);
                catgt_path = fullfile(rootZ, catgt_output);
                if exist(catgt_path, "file")
                    delete(catgt_path);
                end
            end
            % add tcat_imecN.ap.xd*.txt output to imec_tcat_list
            tcat_imec_str = sprintf("*tcat.%s.ap.xd*.txt", imecNum);
            tcat_imec = dir(fullfile(rootZ, tcat_imec_str));
            tcat_imec_path = fullfile(rootZ, tcat_imec.name);
            % convert to string
            tcat_imec_path = string(tcat_imec_path);
            % append string to imec_tcat_list without combining the strings only if not already in list
            if ~any(strcmp(tprime_struct.imec_tcat_list, tcat_imec_path))
                tprime_struct.imec_tcat_list = [tprime_struct.imec_tcat_list, tcat_imec_path];
            end

            % run extract_waveforms.bat on temp_wh.dat (or temp_wh_cat.dat) file
            if extract_waveforms
               cd(kilosortFolder)
               extractCommand = sprintf('extract_waveforms.bat %s/params.py',...
                                                        finalDestFolder);
               fprintf('  Bash command: %s\n', extractCommand)
               system(extractCommand);
            end

            % delete temp_wh.dat file
            if deleteTemp; fprintf('\tDeleting temp_wh.dat...\n'); delete(ops.fproc); end
            
            % if TPrime, convert spike times to seconds
            if runTPrime
                fprintf('\tConverting spike times to seconds...\n')
                spike_times = readNPY(fullfile(finalDestFolder, 'spike_times.npy'));
                % keep precision to maximum decimal places
                spike_times_sec = double(spike_times) / sample_rate;
                % write to file with each spike time on a new line
                spike_times_sec_file = fullfile(finalDestFolder, "spike_times_sec.txt");
                fileID = fopen(spike_times_sec_file, 'w');
                fprintf(fileID, '%f\n', spike_times_sec);
                fprintf('\t\tGenerating %s\n', spike_times_sec_file)
                fprintf('\t\tDone.\n')
                tprime_struct.spiketime_sec_files = [tprime_struct.spiketime_sec_files, spike_times_sec_file];
                tprime_struct.sample_rates = [tprime_struct.sample_rates, sample_rate];
            end
        end
    end

    % run TPrime
    if runTPrime && ~isempty(tprime_struct.nidq_tcat)
        fprintf('Running TPrime on %s\n', sessionFolder)
        cd(fullfile(kilosortFolder, "TPrime-win/"));
        TPrimeCommand = sprintf('runit.bat -syncperiod=1.0 -tostream=%s',...
                        fullfile(sessionPath, tprime_struct.nidq_tcat.name));
        if ~isempty(tprime_struct.imec_tcat_list) && length(tprime_struct.imec_tcat_list) == length(tprime_struct.spiketime_sec_files)
            for j = 1:length(tprime_struct.imec_tcat_list)
                tprime_imec_tcat = tprime_struct.imec_tcat_list(j);
                tprime_sec_file = tprime_struct.spiketime_sec_files(j);
                % output file name
                tprime_sec_final = strrep(tprime_sec_file, '.txt', '_adj.txt');
                TPrimeCommand = strcat(TPrimeCommand, sprintf(' -fromstream=%d,%s', j, tprime_imec_tcat));
                TPrimeCommand = strcat(TPrimeCommand, sprintf(' -events=%d,%s,%s', j, tprime_sec_file, tprime_sec_final));
                tprime_struct.spiketime_sec_adj_files = [tprime_struct.spiketime_sec_adj_files, tprime_sec_final];
            end
            % system command for TPrime
            fprintf('  Bash command: %s\n', TPrimeCommand)
            system(TPrimeCommand);
            % read new spike times from file
            for j = 1:length(tprime_struct.spiketime_sec_adj_files)
                t_sample_rate = tprime_struct.sample_rates(j);
                tprime_sec_adj_file = tprime_struct.spiketime_sec_adj_files(j);  
                fileID = fopen(tprime_sec_adj_file, 'r');
                tprime_sec_adj = textscan(fileID, '%s');
                fclose(fileID);
                % multiply by sample rate to get back to samples
                fprintf('  Generating adjusted spiketime files for: %s\n', tprime_sec_adj_file)
                spike_times_adj = str2double(tprime_sec_adj{1}) * t_sample_rate;
                % convert back to int and write to npy file in appropriate imec folder
                spike_times_adj = uint64(spike_times_adj);
                npy_file = strrep(tprime_sec_adj_file, '_sec_adj.txt', '_adj.npy');
                writeNPY(spike_times_adj, npy_file);
            end
        else
            fprintf('TPrime not running. Check tprime_struct - imec_tcat_list or spiketime_sec_files\n');
        end
    elseif runTPrime & ~isempty(tprime_struct.nidq_tcat)
        fprintf('   WARNING: Missing tcat.nidq.xd file. TPrime will not run.\n')
    end
end
%% 
