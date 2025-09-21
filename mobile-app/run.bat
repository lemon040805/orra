@echo off
echo Starting Language Learning Mobile App...
echo.

echo Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please run setup.bat first.
    pause
    exit /b 1
)

echo Node.js found!
echo.

echo Installing dependencies...
call npm install

echo.
echo Starting Metro bundler...
start "Metro" cmd /k "npm start"

echo.
echo Choose your platform:
echo 1. Android
echo 2. iOS (requires macOS)
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo Starting Android app...
    call npm run android
) else if "%choice%"=="2" (
    echo Starting iOS app...
    call npm run ios
) else (
    echo Invalid choice. Please run the script again.
)

pause