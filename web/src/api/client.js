import { mockRequest, mockRequestBlob } from "./mockGateway.js";

const isProd = import.meta.env.PROD;
const defaultBase = import.meta.env.VITE_API_BASE || (isProd ? "/api" : "http://127.0.0.1:8000/api");
const defaultMode = "remote";

const config = {
  mode: defaultMode,
  baseUrl: localStorage.getItem("ss_web_api_base_url") || defaultBase,
};

if (isProd && config.mode !== "remote") {
  config.mode = "remote";
  localStorage.setItem("ss_web_api_mode", "remote");
}
if (isProd && !localStorage.getItem("ss_web_api_base_url")) {
  localStorage.setItem("ss_web_api_base_url", defaultBase);
}

export function configureApi(next) {
  Object.assign(config, next || {});
  if (next?.mode) localStorage.setItem("ss_web_api_mode", next.mode);
  if (next?.baseUrl !== undefined) localStorage.setItem("ss_web_api_base_url", next.baseUrl);
}

export function getApiConfig() {
  return { ...config, isProd };
}

function isFormData(data) {
  return typeof FormData !== "undefined" && data instanceof FormData;
}

function buildUrl(path, data = {}) {
  const base = config.baseUrl || "/api";
  const url = new URL(`${base}${path.startsWith("/") ? path : `/${path}`}`, window.location.origin);
  Object.entries(data || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  });
  return url;
}

function authHeaders(session, includeJson = true) {
  return {
    ...(includeJson ? { "Content-Type": "application/json" } : {}),
    Authorization: session?.token ? `Bearer ${session.token}` : "",
    "X-Student-Id": session?.studentId || "",
    "X-Role": session?.role || "",
  };
}

function handleUnauthorized(session) {
  if (config.mode !== "remote") return;
  if (!session?.token) return;
  window.dispatchEvent(new CustomEvent("authrequired"));
}

async function readErrorMessage(res, fallback) {
  const body = await res.json().catch(() => null);
  if (!body) return fallback;
  if (typeof body.detail === "string") return body.detail;
  if (typeof body.message === "string") return body.message;
  return fallback;
}

export async function request({ path, method = "GET", data = {}, session }) {
  if (config.mode === "mock") {
    return mockRequest({ path, method, data, session });
  }
  const verb = method.toUpperCase();
  const upload = isFormData(data);
  const url = buildUrl(path, verb === "GET" ? data : {});
  const res = await fetch(url.toString(), {
    method,
    headers: authHeaders(session, !upload),
    body: verb === "GET" ? undefined : upload ? data : JSON.stringify(data),
  });
  if (res.status === 401) {
    handleUnauthorized(session);
    throw new Error("HTTP 401");
  }
  if (res.status === 429) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "请求过于频繁");
  }
  if (!res.ok) throw new Error(await readErrorMessage(res, `HTTP ${res.status}`));
  return res.json();
}

export async function requestBlob({ path, data = {}, session }) {
  if (config.mode === "mock") {
    return mockRequestBlob({ path, data, session });
  }
  const res = await fetch(buildUrl(path, data).toString(), {
    method: "GET",
    headers: authHeaders(session, false),
  });
  if (res.status === 401) {
    handleUnauthorized(session);
    throw new Error("HTTP 401");
  }
  if (!res.ok) throw new Error(await readErrorMessage(res, `HTTP ${res.status}`));
  return res.blob();
}
