export function createSystemApi(call, { getApiConfig, configureApi }) {
  return {
    getApiConfig,
    configureApi,
    login: (payload) => call({ path: "/auth/login", method: "POST", data: payload }),
    resetPassword: (payload) => call({ path: "/auth/reset-password", method: "POST", data: payload }),
    changePassword: (payload) => call({ path: "/auth/change-password", method: "POST", data: payload }),
    refreshToken: () => call({ path: "/auth/refresh", method: "POST" }),
    getRuntime: () => call({ path: "/runtime" }),
    getSessionInfo: () => call({ path: "/session" }),
  };
}