
:: You can call TPrime three ways:
::
:: 1) > TPrime cmd-line-parameters
:: 2) > runit.bat cmd-line-parameters
:: 3a) Edit parameters in runit.bat, then call it ...
:: 3b) > runit.bat
::
:: This script effectively says:
:: "If there are no parameters sent to runit.bat, call TPrime
:: with the parameters hard coded here, else, pass all of the
:: parameters through to TPrime."
::

@echo off
@setlocal enableextensions
@cd /d "%~dp0"

:: set LOCALARGS=-syncperiod=1.0 ^
:: -tostream=Y:\tptest\time_trans_01_g0_tcat.imec0.ap.SY_301_6_500.txt ^
:: -fromstream=7,Y:\tptest\time_trans_01_g0_tcat.nidq.XA_0_500.txt ^
:: -events=7,Y:\tptest\time_trans_01_g0_tcat.nidq.XA_1_7700.txt,Y:\tptest\out.txt

@REM set LOCALARGS=-syncperiod=1.0 ^
@REM -tostream=C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\gandalf_20240126_g0_tcat.nidq.xd_8_0_500.txt ^
@REM -fromstream=1,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\gandalf_20240126_g0_tcat.imec0.ap.xd_384_6_500.txt ^
@REM -fromstream=2,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\gandalf_20240126_g0_tcat.imec1.ap.xd_384_6_500.txt ^
@REM -events=1,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\spike_times_imec0.npy,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\spike_times_imec0_adj.txt ^
@REM -events=2,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\spike_times_imec1.npy,C:\Users\Milner\OneDrive\Desktop\gandalf_20240126_Tprime_test\spike_times_imec1_adj.txt

if [%1]==[] (set ARGS=%LOCALARGS%) else (set ARGS=%*)

%~dp0TPrime %ARGS%

