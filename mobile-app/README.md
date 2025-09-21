# Language Learning Mobile App

A React Native mobile application for AI-powered language learning with AWS Cognito authentication.

## Features

- User authentication (Login/Signup/Verification)
- AWS Cognito integration
- Mobile-optimized UI
- Cross-platform (iOS/Android)

## Setup

1. Install dependencies:
```bash
npm install
```

2. For iOS:
```bash
cd ios && pod install && cd ..
npm run ios
```

3. For Android:
```bash
npm run android
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # Screen components
└── services/       # API and authentication services
```

## Dependencies

- React Native 0.72.6
- React Navigation 6
- AWS Cognito Identity JS
- TypeScript support

## Configuration

Update AWS Cognito configuration in `src/services/AuthService.ts`:
- UserPoolId: us-east-1_fvNtXNAyp
- ClientId: 5rh6qtboujp6cdslv62as1onbo
- API_BASE_URL: https://r9t9xk38j1.execute-api.us-east-1.amazonaws.com/prod