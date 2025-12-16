@echo off
echo.
echo === Training Planner CLI ===
echo.

:: يفترض هذا البرنامج النصي أنه موجود داخل مجلد 'src'
cd ..
echo Changing directory to project root: %cd%
echo Prechazim do korenoveho adresare projektu: %cd%
echo التبديل إلى جذر المشروع: %cd%

set MAIN_CMD=
set PYTHON_EXE=

:: 1. Searching in PATH (py, python3, python)
:: Hledani v PATH
:: البحث في المسار
where py >nul 2>nul
if not errorlevel 1 set MAIN_CMD=py

if "%MAIN_CMD%"=="" (
    where python3 >nul 2>nul
    if not errorlevel 1 set MAIN_CMD=python3
)

if "%MAIN_CMD%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 set MAIN_CMD=python
)

:: 2. Searching in fixed C:\Program Files locations
:: Hledani v pevnych umistenich C:\Program Files
:: البحث في مواقع C:\Program Files الثابتة
if "%MAIN_CMD%"=="" (
    if exist "C:\Program Files\Python311\python.exe" set PYTHON_EXE="C:\Program Files\Python311\python.exe"
    if exist "C:\Program Files\Python310\python.exe" set PYTHON_EXE="C:\Program Files\Python310\python.exe"
    if exist "C:\Program Files\Python39\python.exe" set PYTHON_EXE="C:\Program Files\Python39\python.exe"
)

:: --- EXECUTION ---
:: Spusteni
:: التنفيذ
if not "%MAIN_CMD%"=="" (
    echo Found via PATH: %MAIN_CMD%
    %MAIN_CMD% src/cli.py
) else if not "%PYTHON_EXE%"=="" (
    echo Found directly: %PYTHON_EXE%
    %PYTHON_EXE% src/cli.py
) else (
    echo =======================================================
    echo CRITICAL ERROR: Python not found. Project cannot run.
    echo KRITICKA CHYBA: Python nenalezen. Projekt nelze spustit.
    echo خطأ فادح: لم يتم العثور على بايثون. لا يمكن تشغيل المشروع.
    echo =======================================================
)


pause
