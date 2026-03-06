const THEME_STORAGE_KEY = "dashboard_theme";
const SUPPORTED_THEMES = ["classic", "black", "light"];

const ids = {
  form: document.getElementById("settingsForm"),
  submit: document.getElementById("saveSettingsButton"),
  message: document.getElementById("settingsMessage"),
  details: document.getElementById("settingsDetails"),
  language: document.getElementById("language"),
  theme: document.getElementById("theme"),
  mediaBasePath: document.getElementById("mediaBasePath"),
  useBasePathDefaults: document.getElementById("useBasePathDefaults"),
  sabDownloadDir: document.getElementById("sabDownloadDir"),
  sabCompleteDir: document.getElementById("sabCompleteDir"),
  autoConfigureAppLinks: document.getElementById("autoConfigureAppLinks"),
  radarrSabCategory: document.getElementById("radarrSabCategory"),
  sonarrSabCategory: document.getElementById("sonarrSabCategory"),
  homePublicIp: document.getElementById("homePublicIp"),
  vpnExpectedIp: document.getElementById("vpnExpectedIp"),
  vpnExpectedIps: document.getElementById("vpnExpectedIps"),
  vpnOrgKeywords: document.getElementById("vpnOrgKeywords"),
};

function normalizeTheme(value) {
  if (!value) {
    return "classic";
  }
  const next = String(value).toLowerCase().trim();
  return SUPPORTED_THEMES.includes(next) ? next : "classic";
}

function detectInitialTheme() {
  try {
    const rawSaved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (rawSaved) {
      return normalizeTheme(rawSaved);
    }
  } catch (_error) {
    // Ignore blocked storage and use fallback below.
  }
  return "classic";
}

function setTheme(theme, persist = true) {
  const next = normalizeTheme(theme);
  document.documentElement.dataset.theme = next;
  if (ids.theme && ids.theme.value !== next) {
    ids.theme.value = next;
  }
  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch (_error) {
      // Ignore write failures.
    }
  }
}

function asText(value) {
  return String(value ?? "").trim();
}

function normalizePath(value) {
  let text = asText(value).replace(/\\/g, "/");
  while (text.includes("//")) {
    text = text.replace(/\/\//g, "/");
  }
  if (text.length > 1 && text.endsWith("/")) {
    text = text.slice(0, -1);
  }
  return text;
}

function applyBasePathDefaults() {
  if (!ids.useBasePathDefaults.checked) {
    return;
  }
  const base = normalizePath(ids.mediaBasePath.value);
  if (!base || !base.startsWith("/")) {
    return;
  }
  ids.sabDownloadDir.value = `${base}/downloads/incomplete`;
  ids.sabCompleteDir.value = `${base}/downloads/complete`;
}

function setMessage(text, isError = false) {
  ids.message.classList.remove("hidden", "ok", "error");
  ids.message.classList.add(isError ? "error" : "ok");
  ids.message.textContent = text;
}

function setDetails(payload) {
  if (!payload) {
    ids.details.classList.add("hidden");
    ids.details.textContent = "";
    return;
  }
  ids.details.classList.remove("hidden");
  ids.details.textContent = JSON.stringify(payload, null, 2);
}

async function apiGet(path) {
  const response = await fetch(path, { cache: "no-store" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function apiPost(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok && data.ok !== false, status: response.status, data };
}

function collectPayload() {
  return {
    language: asText(ids.language.value) || "en",
    theme: normalizeTheme(ids.theme.value),
    mediaBasePath: normalizePath(ids.mediaBasePath.value),
    useBasePathDefaults: ids.useBasePathDefaults.checked,
    sabDownloadDir: asText(ids.sabDownloadDir.value),
    sabCompleteDir: asText(ids.sabCompleteDir.value),
    autoConfigureAppLinks: ids.autoConfigureAppLinks.checked,
    radarrSabCategory: asText(ids.radarrSabCategory.value),
    sonarrSabCategory: asText(ids.sonarrSabCategory.value),
    homePublicIp: asText(ids.homePublicIp.value),
    vpnExpectedIp: asText(ids.vpnExpectedIp.value),
    vpnExpectedIps: asText(ids.vpnExpectedIps.value),
    vpnOrgKeywords: asText(ids.vpnOrgKeywords.value),
  };
}

function fillFields(settings) {
  const source = settings || {};
  ids.language.value = asText(source.language) || "en";
  ids.theme.value = normalizeTheme(source.theme);
  ids.mediaBasePath.value = asText(source.mediaBasePath);
  ids.useBasePathDefaults.checked = source.useBasePathDefaults !== false;
  ids.sabDownloadDir.value = asText(source.sabDownloadDir);
  ids.sabCompleteDir.value = asText(source.sabCompleteDir);
  ids.autoConfigureAppLinks.checked = source.autoConfigureAppLinks !== false;
  ids.radarrSabCategory.value = asText(source.radarrSabCategory);
  ids.sonarrSabCategory.value = asText(source.sonarrSabCategory);
  ids.homePublicIp.value = asText(source.homePublicIp);
  ids.vpnExpectedIp.value = asText(source.vpnExpectedIp);
  ids.vpnExpectedIps.value = asText(source.vpnExpectedIps);
  ids.vpnOrgKeywords.value = asText(source.vpnOrgKeywords);
}

async function bootstrap() {
  try {
    const status = await apiGet("/api/settings");
    fillFields(status.settings || {});
    setTheme(status.settings?.theme || detectInitialTheme(), false);
    const lastApply = status.lastApply || {};
    if (lastApply.at) {
      const warnings = lastApply.warnings || [];
      const errors = lastApply.errors || [];
      if (errors.length > 0) {
        setMessage(`Last save had errors: ${errors.join(" | ")}`, true);
        setDetails(lastApply.results || null);
      } else if (warnings.length > 0) {
        setMessage(`Last save had warnings: ${warnings.join(" | ")}`, false);
        setDetails(lastApply.results || null);
      }
    }
  } catch (error) {
    setMessage(`Failed to load settings: ${error.message}`, true);
    setTheme(detectInitialTheme(), false);
  }
}

ids.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  ids.submit.disabled = true;
  const payload = collectPayload();
  setDetails(null);

  try {
    const response = await apiPost("/api/settings/save", payload);
    if (!response.ok || !response.data.ok) {
      const errors = response.data.errors || [];
      const joined = errors.length > 0 ? `: ${errors.join(" | ")}` : "";
      setMessage(`Save failed${joined}`, true);
      setDetails(response.data);
      return;
    }

    localStorage.setItem("dashboard_language", payload.language);
    setTheme(ids.theme.value, true);
    const warnings = response.data.warnings || [];
    if (warnings.length > 0) {
      setMessage(`Settings saved with warnings: ${warnings.join(" | ")}`, false);
    } else {
      setMessage("Settings saved successfully.", false);
    }
    setDetails(response.data.results || null);
  } catch (error) {
    setMessage(`Save request failed: ${error.message}`, true);
  } finally {
    ids.submit.disabled = false;
  }
});

ids.mediaBasePath.addEventListener("input", applyBasePathDefaults);
ids.useBasePathDefaults.addEventListener("change", () => {
  applyBasePathDefaults();
});
ids.theme.addEventListener("change", (event) => {
  setTheme(event.target.value, true);
});

setTheme(detectInitialTheme(), false);
bootstrap();
