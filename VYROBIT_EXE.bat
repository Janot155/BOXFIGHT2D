@echo off
chcp 65001 >nul
title Vytváření Box Fight 2D EXE s automatickými aktualizacemi
cd /d "%~dp0"

echo =========================================
echo   BOX FIGHT 2D - VYROBIT EXE
echo =========================================
echo.
if not exist "boxfight.ico" (
  echo CHYBI IKONA boxfight.ico. Vrat ji do teto slozky.
  pause
  exit /b 1
)

echo Instaluji potrebne balicky Pythonu...
py -m pip install --upgrade pip
if errorlevel 1 goto PYERROR
py -m pip install pywebview pyinstaller
if errorlevel 1 goto PYERROR

echo.
echo Vytvarim aplikaci BoxFight2D.exe...
py -m PyInstaller --noconfirm --clean --onefile --windowed --icon "boxfight.ico" --name BoxFight2D --add-data "index.html;." game.py
if errorlevel 1 goto BUILDERROR

echo.
echo HOTOVO! EXE soubor najdes tady:
echo %~dp0dist\BoxFight2D.exe
echo.
pause
exit /b 0

:PYERROR
echo.
echo Chyba pri instalaci balicku. Over, ze mas Python 3.10 nebo novejsi
echo a pri instalaci Pythonu bylo zapnute Add Python to PATH.
pause
exit /b 1

:BUILDERROR
echo.
echo Vytvoreni EXE se nepovedlo. Vyslednou chybu muzes zkopirovat a poslat mi.
pause
exit /b 1
