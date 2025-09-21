# Language Learning Mobile App (Expo)

A React Native mobile application for AI-powered language learning with AWS Cognito authentication, built with Expo for easy development and testing.

## Quick Start

1. **Install Node.js** from https://nodejs.org/
2. **Install Expo Go** on your phone:
   - Android: [Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
3. **Run the app**:
   ```bash
   npm install
   npx expo start
   ```
4. **Scan QR code** with Expo Go app

## Features

- User authentication (Login/Signup/Verification)
- AWS Cognito integration
- Mobile-optimized UI
- Cross-platform (iOS/Android)
- Instant testing with Expo Go

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # Screen components
└── services/       # API and authentication services
```

## Configuration

AWS Cognito settings in `src/services/AuthService.ts`:
- UserPoolId: us-east-1_fvNtXNAyp
- ClientId: 5rh6qtboujp6cdslv62as1onbo
- API_BASE_URL: https://r9t9xk38j1.execute-api.us-east-1.amazonaws.com/prod