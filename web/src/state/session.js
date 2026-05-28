const KEY = "ss_web_session_v1";
const DEFAULT_SESSION = { studentId: "", role: "student", token: "" };

export function getSession() {
  const saved = JSON.parse(localStorage.getItem(KEY) || "null");
  if (saved?.studentId || saved?.token) {
    return { ...DEFAULT_SESSION, ...saved };
  }
  setSession(DEFAULT_SESSION);
  return { ...DEFAULT_SESSION };
}

export function setSession(session) {
  localStorage.setItem(KEY, JSON.stringify({ ...DEFAULT_SESSION, ...(session || {}) }));
  window.dispatchEvent(new CustomEvent("sessionchange"));
}
