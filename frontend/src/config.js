export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "",
  cognito: {
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "",
    clientId: import.meta.env.VITE_COGNITO_APP_CLIENT_ID || "",
  },
};
