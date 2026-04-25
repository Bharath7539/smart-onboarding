import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
} from "amazon-cognito-identity-js";
import { config } from "../config";

const STORAGE_KEY = "smart_onboarding_auth";

function getPool() {
  return new CognitoUserPool({
    UserPoolId: config.cognito.userPoolId,
    ClientId: config.cognito.clientId,
  });
}

export function loginWithCognito(email, password) {
  return new Promise((resolve, reject) => {
    const userPool = getPool();
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });

    cognitoUser.authenticateUser(authDetails, {
      onSuccess: (session) => {
        const idTokenPayload = session.getIdToken().decodePayload();
        const groups = idTokenPayload["cognito:groups"] || [];
        const role = groups.includes("hr-admin") ? "admin" : "employee";
        const authData = {
          email,
          role,
          token: session.getIdToken().getJwtToken(),
          employeeId: idTokenPayload["custom:employee_id"] || null,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(authData));
        resolve(authData);
      },
      onFailure: (err) => reject(err),
      newPasswordRequired: () =>
        reject(
          new Error(
            "Temporary password detected. Please complete first-time password change in Cognito hosted flow."
          )
        ),
    });
  });
}

export function getStoredAuth() {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function logout() {
  localStorage.removeItem(STORAGE_KEY);
}
