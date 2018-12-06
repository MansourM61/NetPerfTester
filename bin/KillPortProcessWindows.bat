@ECHO off
cls
REM ***********************************************************************************************
REM *                                                                                             *
REM *                                                                                             *
REM *    This script is written for OAM preparation setup by Mojtaba Mansour Abadi (Mar 2018)     *
REM *                                                                                             *
REM *    Run this script on the windows PC which is in the vpn relay chain.                        *
REM *                                                                                             *
REM *    Note that this script must be run with administrator privilege.                          *
REM *                                                                                             *
REM *    To do that, right click on the script and select "Run as administrator".                 *
REM *                                                                                             *
REM *                                                                                             *
REM ***********************************************************************************************
REM
REM ***********************************************************************************************
REM *                                                                                             *
REM *                                                                                             *
REM *    This scripts will do the following tasks:                                                *
REM *                                                                                             *
REM *            1- kill a process with given connection port. 		 							  *
REM *                                                                                             *
REM *                                                                                             *
REM ***********************************************************************************************
REM

SETLOCAL EnableExtensions

:FNLOOP1
SET FN1=%tmp%\tmp+%RANDOM%.tmp
IF EXIST %FN1% GOTO :FNLOOP1

:FNLOOP2
SET FN2=%tmp%\tmp+%RANDOM%.tmp
IF EXIST %FN2% GOTO :FNLOOP2

ECHO Checking port %1...

netstat -ano | findstr :%1 > %FN1%

SETLOCAL

FOR /f "delims=" %%a IN (%FN1%) DO (
 FOR %%i in (%%a) DO ( ECHO %%i > %FN2% )
)
FOR /f "delims==" %%a IN (%FN2%) DO (SET id=%%a)

IF "%id%" == "" (
	echo No process is using the port %1.
	del %FN1%
) ELSE (
	ECHO The process %id% is using the port %1.
	taskkill /PID %id% /F
	del %FN1%
	del %FN2%
REM	tskill %id%
)

TIMEOUT /t 1 /nobreak > NUL