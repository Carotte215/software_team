import { createApp } from "vue";
import App from "./App.vue";
import { configureApi } from "./api/client.js";
import "../styles.css";

if (import.meta.env.PROD && import.meta.env.VITE_API_BASE_URL) {
  configureApi({ mode: "remote", baseUrl: import.meta.env.VITE_API_BASE_URL });
}

function setupPressFeedback() {
  document.addEventListener("pointerdown", (event) => {
    const target = event.target.closest("button, .nav a, .mobile-tabs a, .card[role='button']");
    if (!target || target.disabled) return;
    const rect = target.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const dot = document.createElement("span");
    dot.className = "ripple-dot";
    dot.style.width = `${size}px`;
    dot.style.height = `${size}px`;
    dot.style.left = `${event.clientX - rect.left}px`;
    dot.style.top = `${event.clientY - rect.top}px`;
    target.appendChild(dot);
    window.setTimeout(() => dot.remove(), 620);
  });
}

setupPressFeedback();
createApp(App).mount("#app");
