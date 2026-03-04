const ids = {
  form: document.getElementById("settingsForm"),
  submit: document.getElementById("saveSettingsButton"),
  message: document.getElementById("settingsMessage"),
  details: document.getElementById("settingsDetails"),
  language: document.getElementById("language"),
  mediaBasePath: document.getElementById("mediaBasePath"),
  useBasePathDefaults: document.getElementById("useBasePathDefaults"),
  radarrRootPath: document.getElementById("radarrRootPath"),
  sonarrRootPath: document.getElementById("sonarrRootPath"),
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
  ids.radarrRootPath.value = `${base}/movies`;
  ids.sonarrRootPath.value = `${base}/tv`;
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
    mediaBasePath: normalizePath(ids.mediaBasePath.value),
    useBasePathDefaults: ids.useBasePathDefaults.checked,
    radarrRootPath: asText(ids.radarrRootPath.value),
    sonarrRootPath: asText(ids.sonarrRootPath.value),
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
  ids.mediaBasePath.value = asText(source.mediaBasePath);
  ids.useBasePathDefaults.checked = source.useBasePathDefaults !== false;
  ids.radarrRootPath.value = asText(source.radarrRootPath);
  ids.sonarrRootPath.value = asText(source.sonarrRootPath);
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

bootstrap();
