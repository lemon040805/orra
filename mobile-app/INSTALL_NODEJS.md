# Install Node.js to Run the Mobile App

Node.js is not installed on your system. Follow these steps:

## Step 1: Download Node.js
1. Go to https://nodejs.org/
2. Download the LTS version (recommended)
3. Run the installer and follow the setup wizard

## Step 2: Verify Installation
Open Command Prompt and run:
```
node --version
npm --version
```

## Step 3: Install Dependencies
Navigate to the mobile-app folder and run:
```
cd c:\Users\yeong\orra\mobile-app
npm install
```

## Step 4: Run the App
```
npm start
```

Then in another terminal:
```
npm run android
```

## Alternative: Use Expo (Easier Setup)
If you want a simpler setup, I can convert this to an Expo project which requires less configuration.