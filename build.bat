@echo off
chcp 936 >nul
setlocal EnableExtensions

set "root=%~dp0"
cd /d "%root%"

echo ===================================
echo VoiceMagic build script (Windows)
echo ===================================
echo.

echo [1/4] Frontend build...
if not exist "frontend\package.json" call :die "Missing frontend\\package.json"
where npm >nul 2>nul
if errorlevel 1 call :die "npm not found. Install Node.js first."
rd /s /q "backend\dist" >nul 2>&1
pushd "frontend" || call :die "Cannot enter frontend directory"
if not exist "node_modules" call npm install
if errorlevel 1 call :die "npm install failed"
call npm run build
if errorlevel 1 call :die "npm run build failed"
popd
if not exist "backend\dist\index.html" call :die "Missing backend\\dist\\index.html. Check Vite outDir."

echo [2/4] Backend env...
if not exist "backend\requirements.txt" call :die "Missing backend\\requirements.txt"
where python >nul 2>nul
if errorlevel 1 call :die "python not found. Install Python 3.10+ first."
pushd "backend" || call :die "Cannot enter backend directory"
if not exist "previews" mkdir previews

if not exist "venv\\Scripts\\activate.bat" python -m venv venv
if errorlevel 1 call :die "Failed to create venv"
call venv\Scripts\activate.bat
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python -m pip install -r requirements.txt
if errorlevel 1 call :die "pip install -r requirements.txt failed"
python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 python -m pip install pyinstaller
if errorlevel 1 call :die "PyInstaller install failed"

echo [3/4] PyInstaller build...
rd /s /q pyinstaller_dist >nul 2>&1
rd /s /q pyinstaller_build >nul 2>&1
del /q VoiceMagic.spec >nul 2>&1
pyinstaller --onefile --name "VoiceMagic" --distpath "pyinstaller_dist" --workpath "pyinstaller_build" --add-data "dist;dist" --add-data ".env.example;." --add-data "previews;previews" main.py
if errorlevel 1 call :die "PyInstaller build failed"
deactivate

echo [4/4] Preparing output...
if not exist "output" mkdir output
copy /y pyinstaller_dist\VoiceMagic.exe output\ >nul
if errorlevel 1 call :die "Failed to copy VoiceMagic.exe"
copy /y .env.example output\.env >nul
if errorlevel 1 call :die "Failed to copy .env.example"

> output\run.bat echo @echo off
>> output\run.bat echo cd /d "%%~dp0"
>> output\run.bat echo start VoiceMagic.exe
>> output\run.bat echo echo Open http://localhost:8000
>> output\run.bat echo pause

popd
echo.
echo ===================================
echo Done
echo Output: %root%backend\output
echo ===================================
pause
exit /b 0

:die
echo.
echo ERROR: %~1
echo.
pause
exit /b 1
