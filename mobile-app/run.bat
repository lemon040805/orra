@echo off
echo Starting Language Learning Mobile App with Expo...
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
echo Starting Expo development server...
echo.
echo Instructions:
echo 1. Install Expo Go app on your phone
echo 2. Scan the QR code that appears
echo 3. The app will load on your phone
echo.

call npx expo start

pause