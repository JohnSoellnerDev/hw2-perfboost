@echo off
setlocal EnableDelayedExpansion
title FNAF: Help Wanted 2 - HW2-PerfBoost Installer

echo ============================================================
echo    FNAF: Help Wanted 2 - HW2-PerfBoost Installer (Windows)
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PRESETS_DIR=%SCRIPT_DIR%presets"
set "GAME_DIR="

:: Auto-detect Steam installation via Registry
set "STEAM_DIR="
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul') do set "STEAM_DIR=%%B"
if not defined STEAM_DIR (
    for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v InstallPath 2^>nul') do set "STEAM_DIR=%%B"
)
if defined STEAM_DIR (
    set "STEAM_DIR=!STEAM_DIR:/=\!"
    if exist "!STEAM_DIR!\steamapps\common\HW2\Thumper\Content\Paks" (
        set "GAME_DIR=!STEAM_DIR!\steamapps\common\HW2"
    ) else if exist "!STEAM_DIR!\steamapps\libraryfolders.vdf" (
        for /f "usebackq tokens=1,2 delims=	 " %%I in ("!STEAM_DIR!\steamapps\libraryfolders.vdf") do (
            if "%%~I"=="path" (
                set "LIB=%%~J"
                set "LIB=!LIB:\\=\!"
                if exist "!LIB!\steamapps\common\HW2\Thumper\Content\Paks" (
                    set "GAME_DIR=!LIB!\steamapps\common\HW2"
                )
            )
        )
    )
)

:: Fallback common paths
if not defined GAME_DIR (
    for %%D in (C D E F G) do (
        if exist "%%D:\SteamLibrary\steamapps\common\HW2\Thumper\Content\Paks" set "GAME_DIR=%%D:\SteamLibrary\steamapps\common\HW2"
        if exist "%%D:\Program Files (x86)\Steam\steamapps\common\HW2\Thumper\Content\Paks" set "GAME_DIR=%%D:\Program Files (x86)\Steam\steamapps\common\HW2"
    )
)

if defined GAME_DIR (
    echo [OK] Found Help Wanted 2 at:
    echo      !GAME_DIR!
) else (
    echo [!] Could not auto-detect Help Wanted 2.
    set /p "GAME_DIR=Paste the full path to your HW2 folder (containing HW2.exe): "
    set "GAME_DIR=!GAME_DIR:"=!"
)

set "PAKS_DIR=!GAME_DIR!\Thumper\Content\Paks"
set "MODS_DIR=!PAKS_DIR!\~mods"

if not exist "!PAKS_DIR!" (
    echo.
    echo [ERROR] Could not find "!PAKS_DIR!".
    echo Please make sure you selected the main HW2 folder.
    pause
    exit /b 1
)

echo.
echo Choose a preset to install:
echo   1) NativeQuality (Recommended - Max Visuals) - 1.58x-1.76x FPS at 100%% NATIVE resolution (zero upscaling!)
echo   2) Balanced      (Recommended - High FPS/VR) - 2.07x-2.24x FPS (80%% Fast TAAU Flat / 2x MSAA VR)
echo   3) UltraPerf                                 - 2.21x-2.37x FPS (75%% Fast TAAU / Low-End GPU / High-Hz VR)
echo   4) Uninstall                                 - Remove HW2-PerfBoost and restore stock
echo.
set "CHOICE=1"
set /p "CHOICE=Selection [1-4, default=1]: "

if "!CHOICE!"=="4" (
    if exist "!MODS_DIR!\HW2PerfBoost_*.pak" del /f /q "!MODS_DIR!\HW2PerfBoost_*.pak"
    echo.
    echo [OK] HW2-PerfBoost uninstalled cleanly. Game restored to stock!
    pause
    exit /b 0
)

set "PAK_FILE="
if "!CHOICE!"=="1" set "PAK_FILE=HW2PerfBoost_NativeQuality_P.pak"
if "!CHOICE!"=="2" set "PAK_FILE=HW2PerfBoost_Balanced_P.pak"
if "!CHOICE!"=="3" set "PAK_FILE=HW2PerfBoost_UltraPerf_P.pak"

if not defined PAK_FILE (
    echo [ERROR] Invalid selection.
    pause
    exit /b 1
)

if not exist "!PRESETS_DIR!\!PAK_FILE!" (
    echo [ERROR] Missing preset file: "!PRESETS_DIR!\!PAK_FILE!"
    pause
    exit /b 1
)

if not exist "!MODS_DIR!" mkdir "!MODS_DIR!"
if exist "!MODS_DIR!\HW2PerfBoost_*.pak" del /f /q "!MODS_DIR!\HW2PerfBoost_*.pak"
copy /y "!PRESETS_DIR!\!PAK_FILE!" "!MODS_DIR!\!PAK_FILE!" >nul

echo.
echo [SUCCESS] Installed !PAK_FILE! to:
echo           !MODS_DIR!\!PAK_FILE!
echo.
echo Launch Help Wanted 2 normally via Steam (VR or Flat Mode).
echo Run this script again anytime to switch presets or uninstall.
echo.
pause
exit /b 0
