import {CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserAttribute} from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: 'us-east-1_fvNtXNAyp',
  ClientId: '5rh6qtboujp6cdslv62as1onbo',
};

const userPool = new CognitoUserPool(poolData);
const API_BASE_URL = 'https://r9t9xk38j1.execute-api.us-east-1.amazonaws.com/prod';

export interface AuthResult {
  success: boolean;
  message: string;
  user?: CognitoUser;
}

export class AuthService {
  static async login(email: string, password: string): Promise<AuthResult> {
    return new Promise((resolve) => {
      const authenticationData = {
        Username: email,
        Password: password,
      };

      const authenticationDetails = new AuthenticationDetails(authenticationData);
      const userData = {
        Username: email,
        Pool: userPool,
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: () => {
          resolve({
            success: true,
            message: 'Login successful!',
            user: cognitoUser,
          });
        },
        onFailure: (err) => {
          resolve({
            success: false,
            message: err.message || 'Login failed',
          });
        },
      });
    });
  }

  static async signup(name: string, email: string, password: string): Promise<AuthResult> {
    return new Promise((resolve) => {
      const attributeList = [
        new CognitoUserAttribute({
          Name: 'name',
          Value: name,
        }),
        new CognitoUserAttribute({
          Name: 'email',
          Value: email,
        }),
      ];

      userPool.signUp(email, password, attributeList, [], (err, result) => {
        if (err) {
          resolve({
            success: false,
            message: err.message || 'Signup failed',
          });
          return;
        }

        resolve({
          success: true,
          message: 'Account created! Please check your email for verification code.',
          user: result?.user,
        });
      });
    });
  }

  static async verifyAccount(email: string, code: string): Promise<AuthResult> {
    return new Promise((resolve) => {
      const userData = {
        Username: email,
        Pool: userPool,
      };

      const cognitoUser = new CognitoUser(userData);

      cognitoUser.confirmRegistration(code, true, (err) => {
        if (err) {
          resolve({
            success: false,
            message: err.message || 'Verification failed',
          });
          return;
        }

        resolve({
          success: true,
          message: 'Account verified successfully!',
        });
      });
    });
  }
}