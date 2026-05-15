import { mockRequest } from "./mockGateway.js";

const config = {
  mode: localStorage.getItem("ss_web_api_mode") || "mock",
  baseUrl: localStorage.getItem("ss_web_api_base_url") || "",
};

export function configureApi(next) {
  Object.assign(config, next || {});
}

export async function request({ path, method = "GET", data = {}, session }) {
  if (config.mode === "mock") {
    return mockRequest({ path, method, data, session });
  }
  const verb = method.toUpperCase();
  const url = new URL(`${config.baseUrl}${path.startsWith("/") ? path : `/${path}`}`, window.location.origin);
  if (verb === "GET") {
    Object.entries(data || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
    });
  }
  const res = await fetch(url.toString(), {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: session?.token ? `Bearer ${session.token}` : "",
      "X-Student-Id": session?.studentId || "",
      "X-Role": session?.role || "student",
    },
    body: verb === "GET" ? undefined : JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
