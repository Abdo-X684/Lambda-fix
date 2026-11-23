@echo off
setlocal EnableExtensions EnableDelayedExpansion
title BHL + OP4 - original soundtrack setup

REM Copy ONLY the original Opposing Force MP3 files from the installed game.
REM No music file is generated, downloaded, renamed, or bundled in this ZIP.
set "MODDIR=%~dp0"
pushd "%MODDIR%.."
if errorlevel 1 (
  echo ERROR: could not find the Half-Life folder above this mod folder.
  goto :fail
)
set "HLROOT=%CD%"
popd
set "DEST=%MODDIR%media"
if not exist "%DEST%" mkdir "%DEST%"

echo Half-Life root: %HLROOT%
echo Mod media folder: %DEST%
echo.

set "SOURCES=%HLROOT%\gearbox\media|%HLROOT%\gearbox_downloads\media|%HLROOT%\gearbox_hd\media"
for %%S in ("%HLROOT%\gearbox\media" "%HLROOT%\gearbox_downloads\media" "%HLROOT%\gearbox_hd\media") do (
  if exist "%%~S\*.mp3" (
    echo Copying original OP4 MP3 files from %%~S ...
    for %%F in ("%%~S\*.mp3") do (
      if not exist "%DEST%\%%~nxF" copy /Y "%%~F" "%DEST%\%%~nxF" >nul
    )
  )
)

set "COUNT=0"
for %%F in ("%DEST%\*.mp3") do set /A COUNT+=1
if "!COUNT!"=="0" (
  echo.
  echo ERROR: no MP3 files found in the installed gearbox media folders.
  echo Install Opposing Force ^(appid 50^), then run this script again.
  echo The script deliberately does NOT copy Half-Life base media or invent music.
  goto :fail
)

if exist "%DEST%\gamestartup.mp3" (
  echo Startup music: gamestartup.mp3 found in the installed OP4 copy.
) else (
  echo Startup music: gamestartup.mp3 is not provided by this installation;
  echo map CD tracks were still copied. Nothing was fabricated.
)

> "%DEST%\SOURCE.txt" echo Original OP4 MP3s copied from installed gearbox media folders only.
>> "%DEST%\SOURCE.txt" echo Sources checked: gearbox\media, gearbox_downloads\media, gearbox_hd\media.
>> "%DEST%\SOURCE.txt" echo No valve media, no downloaded music, and no generated MP3 was used.
echo.
echo Done: !COUNT! original OP4 MP3 files are now in "%DEST%".
echo Start with: hl.exe -game lambda-fix -console
exit /b 0

:fail
echo.
echo Setup failed. No music was fabricated or substituted.
exit /b 1
