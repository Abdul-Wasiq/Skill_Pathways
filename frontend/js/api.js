/**
 * Shared API client. Handles auth token storage and consistent
 * error handling so pages don't duplicate fetch boilerplate.
 *
 * HUMAN CONFIGURATION REQUIRED:
 * If your backend runs somewhere other than http://127.0.0.1:8000,
 * update API_BASE_URL below.
 */
const API_BASE_URL =
  location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://addressed-ppc-subsequent-meets.trycloudflare.com";

/**
 * Escape user-generated text before putting it into innerHTML.
 * Use esc(value) for every dynamic value in a template string.
 */
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Only allow http(s) links; anything else (e.g. javascript:) becomes "#". */
function safeUrl(url) {
  try {
    const u = new URL(url, window.location.origin);
    return u.protocol === "http:" || u.protocol === "https:" ? u.href : "#";
  } catch {
    return "#";
  }
}

const Auth = {
  getToken() {
    return localStorage.getItem("cp_token");
  },
  setSession(token, user) {
    localStorage.setItem("cp_token", token);
    localStorage.setItem("cp_user", JSON.stringify(user));
  },
  getUser() {
    const raw = localStorage.getItem("cp_user");
    return raw ? JSON.parse(raw) : null;
  },
  logout() {
    localStorage.removeItem("cp_token");
    localStorage.removeItem("cp_user");
    window.location.href = "login.html";
  },
  requireLogin() {
    if (!this.getToken()) {
      window.location.href = "login.html";
    }
  },
};

async function apiRequest(path, { method = "GET", body = null, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(
      "Unable to reach the server. Is the backend running at " + API_BASE_URL + "?"
    );
  }

  if (response.status === 401 && auth) {
    // Session invalid/expired — send back to login rather than showing raw JSON.
    Auth.logout();
    throw new Error("Your session has expired. Please log in again.");
  }

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const message = data && data.detail ? data.detail : `Request failed (${response.status}).`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
}

function hideError(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.classList.remove("show");
}

function showSuccess(elementId, message) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 4000);
}

function renderNavbar(activePage) {
  const user = Auth.getUser();
  const el = document.getElementById("navbar");
  if (!el) return;

  const links = [
    [
      "home.html",
      "Home",
      `<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>`
    ],
    [
      "feed.html",
      "Feed",
      `<svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>`
    ],
    [
      "opportunities.html",
      "Jobs",
      `<svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>`
    ],
    [
      "connections.html",
      "Network",
      `<svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>`
    ],
    [
      "notifications.html",
      "Alerts",
      `<svg viewBox="0 0 24 24"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>`
    ],
    [
      "profile.html",
      "Me",
      `<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`
    ],
    [
      "ai-assistant.html",
      "Career AI",
      `<svg viewBox="0 0 24 24"><path d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5z"/></svg>`
    ],
  ];

  if (user && user.role === "admin") {
    links.push([
      "admin.html",
      "Admin",
      `<svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>`
    ]);
  }

  el.innerHTML = `
    <div class="brand">CareerBridge</div>
    <nav>
      ${links
        .map(
          ([href, label, icon]) => `
          <a href="${href}" class="${activePage === href ? "active" : ""}">
            ${icon}
            <span>${label}</span>
          </a>
        `
        )
        .join("")}
      ${user ? `<a href="#" id="logoutLink">Sign Out</a>` : ""}
    </nav>
  `;

  const logoutLink = document.getElementById("logoutLink");
  if (logoutLink) {
    logoutLink.addEventListener("click", (e) => {
      e.preventDefault();
      Auth.logout();
    });
  }
}