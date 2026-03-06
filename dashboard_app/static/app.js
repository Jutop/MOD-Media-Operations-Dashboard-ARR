const DASH_REFRESH_MS = 5000;
const ADMIN_REFRESH_MS = 15000;
const SAB_REFRESH_MS = 1000;
const SAB_LIVE_LIMIT = 5;
const LANG_STORAGE_KEY = "dashboard_language";
const THEME_STORAGE_KEY = "dashboard_theme";
const SUPPORTED_LANGUAGES = ["en", "de"];
const SUPPORTED_THEMES = ["classic", "black", "light"];

const ids = {
  languageSelect: document.getElementById("languageSelect"),
  lastUpdated: document.getElementById("lastUpdated"),
  toast: document.getElementById("toast"),
  sumServices: document.getElementById("sumServices"),
  sumServicesMeta: document.getElementById("sumServicesMeta"),
  sumQueue: document.getElementById("sumQueue"),
  sumLibrary: document.getElementById("sumLibrary"),
  sumUpcoming: document.getElementById("sumUpcoming"),
  sumIssues: document.getElementById("sumIssues"),
  vpnCardPill: document.getElementById("vpnCardPill"),
  vpnReason: document.getElementById("vpnReason"),
  vpnCurrentIp: document.getElementById("vpnCurrentIp"),
  vpnOwner: document.getElementById("vpnOwner"),
  vpnHostIp: document.getElementById("vpnHostIp"),
  vpnTunnelIp: document.getElementById("vpnTunnelIp"),
  vpnProvider: document.getElementById("vpnProvider"),
  vpnWave: document.getElementById("vpnWave"),
  openRadarr: document.getElementById("openRadarr"),
  openSonarr: document.getElementById("openSonarr"),
  openSab: document.getElementById("openSab"),
  openOmbi: document.getElementById("openOmbi"),
  openAllApps: document.getElementById("openAllApps"),
  containerRows: document.getElementById("containerRows"),
  sabPathsForm: document.getElementById("sabPathsForm"),
  sabDownloadDirInput: document.getElementById("sabDownloadDirInput"),
  sabCompleteDirInput: document.getElementById("sabCompleteDirInput"),
  sabLiveQueue: document.getElementById("sabLiveQueue"),
  sabLiveUpdated: document.getElementById("sabLiveUpdated"),
  radarrMeta: document.getElementById("radarrMeta"),
  sonarrMeta: document.getElementById("sonarrMeta"),
  sabMeta: document.getElementById("sabMeta"),
  ombiMeta: document.getElementById("ombiMeta"),
  radarrPill: document.getElementById("radarrPill"),
  sonarrPill: document.getElementById("sonarrPill"),
  sabPill: document.getElementById("sabPill"),
  ombiPill: document.getElementById("ombiPill"),
  radarrCard: document.getElementById("radarrCard"),
  sonarrCard: document.getElementById("sonarrCard"),
  sabCard: document.getElementById("sabCard"),
  ombiCard: document.getElementById("ombiCard"),
  radarrKpis: document.getElementById("radarrKpis"),
  sonarrKpis: document.getElementById("sonarrKpis"),
  sabKpis: document.getElementById("sabKpis"),
  ombiKpis: document.getElementById("ombiKpis"),
  radarrEssential: document.getElementById("radarrEssential"),
  sonarrEssential: document.getElementById("sonarrEssential"),
  sabEssential: document.getElementById("sabEssential"),
  ombiEssential: document.getElementById("ombiEssential")
};

const themeOptions = Array.from(document.querySelectorAll("[data-theme-choice]"));

const I18N = {
  en: {
    "ui.title": "Media Ops Bridge",
    "ui.language": "Language",
    "ui.theme": "Theme",
    "lang.en": "English",
    "lang.de": "Deutsch",
    "theme.classic": "Classic MOD",
    "theme.black": "Black",
    "theme.light": "Light",
    "status.waiting": "Waiting for refresh...",
    "status.updated": "Updated {time}",
    "status.live": "live",
    "status.noStatus": "No status available",
    "status.connecting": "Connecting...",
    "status.checking": "Checking",
    "status.online": "Online",
    "status.offline": "Offline",
    "status.unavailable": "Unavailable",
    "status.running": "Running",
    "status.paused": "Paused",

    "summary.services": "Services",
    "summary.queueJobs": "Queue Jobs",
    "summary.queueHint": "Sonarr + Radarr + SAB",
    "summary.librarySize": "Library Size",
    "summary.libraryHint": "Movies + Series tracked",
    "summary.upcoming": "Upcoming",
    "summary.upcomingHint": "Next 45 days",
    "summary.healthIssues": "Health Issues",
    "summary.healthHint": "Warnings + errors",
    "summary.allReachable": "All services reachable",
    "summary.someOffline": "One or more services offline",

    "panel.containerControls": "Container Controls",
    "panel.containerControlsDesc": "Start, stop, or restart managed containers.",
    "panel.rootFolders": "Root Folders",
    "panel.rootFoldersDesc": "Add or remove root folders for Radarr and Sonarr.",
    "panel.radarrRoots": "Radarr Roots",
    "panel.sonarrRoots": "Sonarr Roots",
    "panel.sabPaths": "SAB Paths",
    "panel.sabPathsDesc": "Manage active SABnzbd download folders.",
    "panel.vpnStatus": "VPN Status",
    "panel.liveSabQueue": "Live SAB Queue",

    "table.service": "Service",
    "table.status": "Status",
    "table.health": "Health",
    "table.actions": "Actions",

    "placeholder.radarrRoot": "/media/Movies",
    "placeholder.sonarrRoot": "/media/tv",
    "placeholder.sabIncomplete": "/media/downloads/incomplete",
    "placeholder.sabComplete": "/media/downloads/complete",

    "sab.incompleteDir": "Incomplete / Active Download Dir",
    "sab.completeDir": "Complete Download Dir",
    "sab.unavailable": "SAB unavailable: {reason}",
    "sab.noActive": "No active downloads right now",
    "sab.left": "Left: {value}",
    "sab.eta": "ETA: {value}",
    "sab.state.downloading": "downloading",
    "sab.state.queued": "queued",
    "sab.state.paused": "paused",
    "sab.state.extracting": "extracting",
    "sab.state.repairing": "repairing",
    "sab.state.moving": "moving",
    "sab.state.fetching": "fetching",
    "sab.state.checking": "checking",
    "sab.state.idle": "idle",

    "vpn.currentEgressIp": "Current Egress IP",
    "vpn.owner": "Owner",
    "vpn.hostIp": "Host IP",
    "vpn.tunnelIp": "Tunnel IP",
    "vpn.provider": "Provider",
    "vpn.on": "VPN ON",
    "vpn.off": "VPN OFF",
    "vpn.unknown": "VPN UNKNOWN",
    "vpn.hostPrefix": "\uD83C\uDFE0",
    "vpn.tunnelPrefix": "\uD83D\uDD12",

    "action.add": "Add",
    "action.saveSabPaths": "Save SAB Paths",
    "action.settings": "Settings",
    "action.openAllTabs": "Open All Tabs",
    "action.start": "start",
    "action.stop": "stop",
    "action.restart": "restart",
    "action.remove": "remove",

    "meta.versionQueueOs": "Version {version} | Queue {queue} | {os}",
    "meta.versionSystemState": "Version {version} | {status} | {state}",
    "meta.offline": "Offline: {error}",
    "meta.ombi": "Version {version} | {framework} | {api}",
    "api.healthy": "API healthy",
    "api.unknown": "API unknown",

    "kpi.library": "Library",
    "kpi.wanted": "Wanted",
    "kpi.downloaded": "Downloaded",
    "kpi.queue": "Queue",
    "kpi.health": "Health",
    "kpi.diskFree": "Disk Free",
    "kpi.series": "Series",
    "kpi.episodes": "Episodes",
    "kpi.speed": "Speed",
    "kpi.eta": "ETA",
    "kpi.completed": "Completed",
    "kpi.failed": "Failed",
    "kpi.requests": "Requests",
    "kpi.pending": "Pending",
    "kpi.approved": "Approved",
    "kpi.available": "Available",
    "kpi.api": "API",

    "essential.status": "Status",
    "essential.queueDownloading": "Queue Downloading",
    "essential.queueImporting": "Queue Importing",
    "essential.upcoming7d30d": "Upcoming 7d / 30d",
    "essential.storage": "Storage",
    "essential.healthIssues": "Health Issues",
    "essential.continuingEnded": "Continuing / Ended",
    "essential.missingEpisodes": "Missing Episodes",
    "essential.queueLeftMb": "Queue Left MB",
    "essential.failedJobs": "Failed Jobs",
    "essential.transferDay": "Transfer Day",
    "essential.transferWeek": "Transfer Week",
    "essential.transferMonth": "Transfer Month",
    "essential.branch": "Branch",
    "essential.database": "Database",
    "essential.storagePath": "Storage",
    "essential.os": "OS",

    "value.healthIssues": "{total} (warn {warnings} / err {errors})",
    "value.upcoming": "{days7} / {days30}",
    "value.continuingEnded": "{continuing} / {ended}",
    "value.storageFree": "{free} free",

    "container.dockerUnavailable": "Docker unavailable",
    "container.state.running": "running",
    "container.state.exited": "exited",
    "container.state.dead": "dead",
    "container.state.stopped": "stopped",
    "container.state.missing": "missing",
    "container.state.created": "created",
    "container.state.restarting": "restarting",
    "container.state.paused": "paused",
    "container.state.removing": "removing",
    "container.state.unknown": "unknown",
    "container.health.healthy": "healthy",
    "container.health.unhealthy": "unhealthy",
    "container.health.starting": "starting",
    "container.actionTriggered": "{service}: {action} triggered",
    "container.rootRemoved": "{service}: root folder removed",

    "root.unavailable": "Unavailable: {reason}",
    "root.none": "No root folders configured",
    "root.entry": "{path} ({free} free)",

    "toast.radarrRootAdded": "Radarr root folder added",
    "toast.sonarrRootAdded": "Sonarr root folder added",
    "toast.sabPathsUpdated": "SAB paths updated",
    "toast.noServiceTabs": "No service tabs available right now",
    "toast.popupBlocked": "Browser blocked popups; allow popups for this page",
    "toast.openedTabs": "Opened {count} tab{suffix}",

    "error.initialLoad": "Initial load failed: {error}",
    "error.refreshDashboard": "Dashboard refresh failed: {error}",
    "error.refreshAdmin": "Admin refresh failed: {error}"
  },
  de: {
    "ui.title": "Media Ops Bridge",
    "ui.language": "Sprache",
    "ui.theme": "Design",
    "lang.en": "Englisch",
    "lang.de": "Deutsch",
    "theme.classic": "Klassisch MOD",
    "theme.black": "Schwarz",
    "theme.light": "Hell",
    "status.waiting": "Warte auf Aktualisierung...",
    "status.updated": "Aktualisiert {time}",
    "status.live": "live",
    "status.noStatus": "Kein Status verf\u00fcgbar",
    "status.connecting": "Verbinde...",
    "status.checking": "Pr\u00fcfe",
    "status.online": "Online",
    "status.offline": "Offline",
    "status.unavailable": "Nicht verf\u00fcgbar",
    "status.running": "L\u00e4uft",
    "status.paused": "Pausiert",

    "summary.services": "Dienste",
    "summary.queueJobs": "Queue-Aufgaben",
    "summary.queueHint": "Sonarr + Radarr + SAB",
    "summary.librarySize": "Bibliotheksgr\u00f6\u00dfe",
    "summary.libraryHint": "Verfolgte Filme + Serien",
    "summary.upcoming": "Bevorstehend",
    "summary.upcomingHint": "N\u00e4chste 45 Tage",
    "summary.healthIssues": "Gesundheitsprobleme",
    "summary.healthHint": "Warnungen + Fehler",
    "summary.allReachable": "Alle Dienste erreichbar",
    "summary.someOffline": "Mindestens ein Dienst offline",

    "panel.containerControls": "Container-Steuerung",
    "panel.containerControlsDesc": "Verwaltete Container starten, stoppen oder neu starten.",
    "panel.rootFolders": "Root-Ordner",
    "panel.rootFoldersDesc": "Root-Ordner f\u00fcr Radarr und Sonarr hinzuf\u00fcgen oder entfernen.",
    "panel.radarrRoots": "Radarr Root-Ordner",
    "panel.sonarrRoots": "Sonarr Root-Ordner",
    "panel.sabPaths": "SAB-Pfade",
    "panel.sabPathsDesc": "Aktive SABnzbd-Downloadordner verwalten.",
    "panel.vpnStatus": "VPN-Status",
    "panel.liveSabQueue": "Live-SAB-Queue",

    "table.service": "Dienst",
    "table.status": "Status",
    "table.health": "Zustand",
    "table.actions": "Aktionen",

    "placeholder.radarrRoot": "/media/Movies",
    "placeholder.sonarrRoot": "/media/tv",
    "placeholder.sabIncomplete": "/media/downloads/incomplete",
    "placeholder.sabComplete": "/media/downloads/complete",

    "sab.incompleteDir": "Unvollst\u00e4ndig / Aktiver Download-Ordner",
    "sab.completeDir": "Fertiger Download-Ordner",
    "sab.unavailable": "SAB nicht verf\u00fcgbar: {reason}",
    "sab.noActive": "Derzeit keine aktiven Downloads",
    "sab.left": "\u00dcbrig: {value}",
    "sab.eta": "ETA: {value}",
    "sab.state.downloading": "l\u00e4dt herunter",
    "sab.state.queued": "in Warteschlange",
    "sab.state.paused": "pausiert",
    "sab.state.extracting": "entpackt",
    "sab.state.repairing": "repariert",
    "sab.state.moving": "verschiebt",
    "sab.state.fetching": "holt",
    "sab.state.checking": "pr\u00fcft",
    "sab.state.idle": "inaktiv",

    "vpn.currentEgressIp": "Aktuelle Egress-IP",
    "vpn.owner": "Besitzer",
    "vpn.hostIp": "Host-IP",
    "vpn.tunnelIp": "Tunnel-IP",
    "vpn.provider": "Anbieter",
    "vpn.on": "VPN AN",
    "vpn.off": "VPN AUS",
    "vpn.unknown": "VPN UNBEKANNT",
    "vpn.hostPrefix": "\uD83C\uDFE0",
    "vpn.tunnelPrefix": "\uD83D\uDD12",

    "action.add": "Hinzuf\u00fcgen",
    "action.saveSabPaths": "SAB-Pfade speichern",
    "action.settings": "Einstellungen",
    "action.openAllTabs": "Alle Tabs \u00f6ffnen",
    "action.start": "starten",
    "action.stop": "stoppen",
    "action.restart": "neu starten",
    "action.remove": "entfernen",

    "meta.versionQueueOs": "Version {version} | Queue {queue} | {os}",
    "meta.versionSystemState": "Version {version} | {status} | {state}",
    "meta.offline": "Offline: {error}",
    "meta.ombi": "Version {version} | {framework} | {api}",
    "api.healthy": "API gesund",
    "api.unknown": "API unbekannt",

    "kpi.library": "Bibliothek",
    "kpi.wanted": "Gesucht",
    "kpi.downloaded": "Heruntergeladen",
    "kpi.queue": "Queue",
    "kpi.health": "Zustand",
    "kpi.diskFree": "Freier Speicher",
    "kpi.series": "Serien",
    "kpi.episodes": "Episoden",
    "kpi.speed": "Geschwindigkeit",
    "kpi.eta": "ETA",
    "kpi.completed": "Abgeschlossen",
    "kpi.failed": "Fehlgeschlagen",
    "kpi.requests": "Anfragen",
    "kpi.pending": "Ausstehend",
    "kpi.approved": "Genehmigt",
    "kpi.available": "Verf\u00fcgbar",
    "kpi.api": "API",

    "essential.status": "Status",
    "essential.queueDownloading": "Queue l\u00e4dt",
    "essential.queueImporting": "Queue importiert",
    "essential.upcoming7d30d": "Kommend 7T / 30T",
    "essential.storage": "Speicher",
    "essential.healthIssues": "Gesundheitsprobleme",
    "essential.continuingEnded": "Laufend / Beendet",
    "essential.missingEpisodes": "Fehlende Episoden",
    "essential.queueLeftMb": "Queue Rest MB",
    "essential.failedJobs": "Fehlgeschlagene Jobs",
    "essential.transferDay": "Transfer Tag",
    "essential.transferWeek": "Transfer Woche",
    "essential.transferMonth": "Transfer Monat",
    "essential.branch": "Branch",
    "essential.database": "Datenbank",
    "essential.storagePath": "Speicher",
    "essential.os": "OS",

    "value.healthIssues": "{total} (warn {warnings} / fehler {errors})",
    "value.upcoming": "{days7} / {days30}",
    "value.continuingEnded": "{continuing} / {ended}",
    "value.storageFree": "{free} frei",

    "container.dockerUnavailable": "Docker nicht verf\u00fcgbar",
    "container.state.running": "l\u00e4uft",
    "container.state.exited": "beendet",
    "container.state.dead": "tot",
    "container.state.stopped": "gestoppt",
    "container.state.missing": "fehlt",
    "container.state.created": "erstellt",
    "container.state.restarting": "startet neu",
    "container.state.paused": "pausiert",
    "container.state.removing": "entfernt",
    "container.state.unknown": "unbekannt",
    "container.health.healthy": "gesund",
    "container.health.unhealthy": "ungesund",
    "container.health.starting": "startet",
    "container.actionTriggered": "{service}: {action} ausgel\u00f6st",
    "container.rootRemoved": "{service}: Root-Ordner entfernt",

    "root.unavailable": "Nicht verf\u00fcgbar: {reason}",
    "root.none": "Keine Root-Ordner konfiguriert",
    "root.entry": "{path} ({free} frei)",

    "toast.radarrRootAdded": "Radarr Root-Ordner hinzugef\u00fcgt",
    "toast.sonarrRootAdded": "Sonarr Root-Ordner hinzugef\u00fcgt",
    "toast.sabPathsUpdated": "SAB-Pfade aktualisiert",
    "toast.noServiceTabs": "Derzeit sind keine Service-Tabs verf\u00fcgbar",
    "toast.popupBlocked": "Browser hat Popups blockiert; Popups f\u00fcr diese Seite erlauben",
    "toast.openedTabs": "{count} Tab(s) ge\u00f6ffnet",

    "error.initialLoad": "Erstladen fehlgeschlagen: {error}",
    "error.refreshDashboard": "Dashboard-Aktualisierung fehlgeschlagen: {error}",
    "error.refreshAdmin": "Admin-Aktualisierung fehlgeschlagen: {error}"
  }
};

const state = {
  dashboard: null,
  admin: null,
  actionInFlight: false,
  language: detectInitialLanguage(),
  theme: detectInitialTheme()
};

function normalizeLanguage(value) {
  if (!value) {
    return "en";
  }
  const short = String(value).toLowerCase().split("-")[0].trim();
  return SUPPORTED_LANGUAGES.includes(short) ? short : "en";
}

function detectInitialLanguage() {
  try {
    const rawSaved = window.localStorage.getItem(LANG_STORAGE_KEY);
    if (rawSaved) {
      return normalizeLanguage(rawSaved);
    }
  } catch (_error) {
    // localStorage can be blocked by browser policies; fallback below.
  }
  return normalizeLanguage(navigator.language);
}

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
    // localStorage can be blocked by browser policies; fallback below.
  }
  return "classic";
}

function currentLocale() {
  return state.language === "de" ? "de-DE" : "en-US";
}

function t(key, params = {}) {
  const langTable = I18N[state.language] || I18N.en;
  const fallback = I18N.en[key];
  let value = langTable[key] ?? fallback ?? key;
  Object.entries(params).forEach(([name, replacement]) => {
    value = value.replace(new RegExp(`\\{${name}\\}`, "g"), String(replacement));
  });
  return value;
}

function applyStaticTranslations() {
  document.title = t("ui.title");

  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    node.textContent = t(key);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    node.setAttribute("placeholder", t(key));
  });
}

function setLanguage(language, persist = true) {
  const next = normalizeLanguage(language);
  state.language = next;
  document.documentElement.lang = next;

  if (ids.languageSelect && ids.languageSelect.value !== next) {
    ids.languageSelect.value = next;
  }

  if (persist) {
    try {
      window.localStorage.setItem(LANG_STORAGE_KEY, next);
    } catch (_error) {
      // Ignore storage write failures.
    }
  }

  applyStaticTranslations();

  if (state.dashboard) {
    renderDashboard(state.dashboard);
  }
  if (state.admin) {
    renderAdmin(state.admin);
  }
}

function setTheme(theme, persist = true) {
  const next = normalizeTheme(theme);
  state.theme = next;
  document.documentElement.dataset.theme = next;

  themeOptions.forEach((button) => {
    const isActive = button.dataset.themeChoice === next;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch (_error) {
      // Ignore storage write failures.
    }
  }
}

function asText(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function asNum(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return "-";
  }
  return num.toLocaleString(currentLocale());
}

function toLocalTime(value) {
  if (!value) {
    return "-";
  }
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) {
    return asText(value);
  }
  return dt.toLocaleString(currentLocale());
}

function showToast(message, isError = false) {
  ids.toast.textContent = message;
  ids.toast.style.borderColor = isError ? "rgba(255, 130, 140, 0.58)" : "rgba(142, 194, 232, 0.45)";
  ids.toast.classList.add("show");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => ids.toast.classList.remove("show"), 2600);
}

function setPill(el, mode, label) {
  el.classList.remove("online", "offline", "unknown", "on", "off");
  el.classList.add(mode || "unknown");
  el.textContent = label;
}

function setCardOnlineState(card, online) {
  card.classList.remove("online", "offline");
  card.classList.add(online ? "online" : "offline");
}

function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function row(cells) {
  const tr = document.createElement("tr");
  cells.forEach((cell) => {
    const td = document.createElement("td");
    if (cell instanceof Node) {
      td.appendChild(cell);
    } else {
      td.textContent = asText(cell);
    }
    tr.appendChild(td);
  });
  return tr;
}

function renderMiniKpis(container, entries) {
  clearNode(container);
  entries.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "kpi";

    const label = document.createElement("span");
    label.textContent = entry.label;

    const value = document.createElement("strong");
    value.textContent = asText(entry.value);

    card.append(label, value);
    container.appendChild(card);
  });
}

function renderEssentialList(listNode, entries) {
  clearNode(listNode);
  if (!entries || entries.length === 0) {
    const li = document.createElement("li");
    const label = document.createElement("span");
    label.className = "label";
    label.textContent = t("essential.status");
    const value = document.createElement("span");
    value.className = "value";
    value.textContent = "-";
    li.append(label, value);
    listNode.appendChild(li);
    return;
  }

  entries.forEach((item) => {
    const li = document.createElement("li");
    const label = document.createElement("span");
    label.className = "label";
    label.textContent = item.label;
    const value = document.createElement("span");
    value.className = "value";
    if (Number.isFinite(item.progressPercent)) {
      value.classList.add("with-progress");

      const valueText = document.createElement("span");
      valueText.className = "progress-value";
      valueText.textContent = asText(item.value);

      const progressWrap = document.createElement("span");
      progressWrap.className = "progress";
      const track = document.createElement("span");
      track.className = "track";
      const fill = document.createElement("span");
      fill.className = "fill";
      const pct = Math.max(0, Math.min(100, Number(item.progressPercent)));
      fill.style.width = `${pct}%`;
      track.appendChild(fill);
      const pctLabel = document.createElement("span");
      pctLabel.className = "label";
      pctLabel.textContent = `${Math.round(pct)}%`;
      progressWrap.append(track, pctLabel);
      value.append(valueText, progressWrap);
    } else {
      value.textContent = asText(item.value);
    }
    li.append(label, value);
    listNode.appendChild(li);
  });
}

function translateSabQueueStatus(status) {
  const normalized = asText(status, "").trim().toLowerCase();
  const key = `sab.state.${normalized}`;
  const translated = t(key);
  return translated === key ? asText(status) : translated;
}

function renderSabLiveQueue(sabService, stamp = null) {
  const queueNode = ids.sabLiveQueue;
  const updatedNode = ids.sabLiveUpdated;
  clearNode(queueNode);

  if (!sabService || !sabService.online) {
    const empty = document.createElement("div");
    empty.className = "sab-live-empty";
    empty.textContent = t("sab.unavailable", {
      reason: asText(sabService?.error, t("status.offline").toLowerCase())
    });
    queueNode.appendChild(empty);
    if (updatedNode) {
      updatedNode.textContent = t("status.offline").toLowerCase();
    }
    return;
  }

  const items = (sabService.queue || []).slice(0, SAB_LIVE_LIMIT);
  if (items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "sab-live-empty";
    empty.textContent = t("sab.noActive");
    queueNode.appendChild(empty);
    if (updatedNode) {
      updatedNode.textContent = stamp ? toLocalTime(stamp) : t("status.live");
    }
    return;
  }

  items.forEach((item) => {
    const wrap = document.createElement("article");
    wrap.className = "sab-live-item";

    const top = document.createElement("div");
    top.className = "sab-live-top";

    const title = document.createElement("div");
    title.className = "sab-live-title";
    title.textContent = asText(item.title);

    const itemState = document.createElement("div");
    itemState.className = "sab-live-state";
    itemState.textContent = translateSabQueueStatus(item.status);

    top.append(title, itemState);

    const meta = document.createElement("div");
    meta.className = "sab-live-meta";
    const left = document.createElement("span");
    left.textContent = t("sab.left", { value: asText(item.sizeLeft) });
    const right = document.createElement("span");
    right.textContent = t("sab.eta", { value: asText(item.timeLeft) });
    meta.append(left, right);

    const track = document.createElement("div");
    track.className = "sab-live-progress";
    const fill = document.createElement("span");
    const pct = Number.isFinite(item.progressPercent) ? Math.max(0, Math.min(100, item.progressPercent)) : 0;
    fill.style.width = `${pct}%`;
    track.appendChild(fill);

    wrap.append(top, meta, track);
    queueNode.appendChild(wrap);
  });

  if (updatedNode) {
    updatedNode.textContent = stamp ? toLocalTime(stamp) : t("status.live");
  }
}

function apiGet(url) {
  return fetch(url, { cache: "no-store" }).then(async (response) => {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  });
}

function apiPost(url, payload) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  });
}

function renderSummary(dashboard) {
  const summary = dashboard.summary || {};
  ids.sumServices.textContent = `${asNum(summary.onlineServices)} / ${asNum(summary.totalServices)}`;
  ids.sumServicesMeta.textContent = summary.onlineServices === summary.totalServices ? t("summary.allReachable") : t("summary.someOffline");
  ids.sumQueue.textContent = asNum(summary.queueTotal);
  ids.sumLibrary.textContent = asNum(summary.libraryTotal);
  ids.sumUpcoming.textContent = asNum(summary.upcomingTotal);
  ids.sumIssues.textContent = asNum(summary.serviceIssues);
}

function ensureQuickLink(id, label, iconSrc, iconAlt) {
  let link = document.getElementById(id);
  if (link) {
    return link;
  }

  const quickLinks = document.querySelector(".quick-links");
  if (!quickLinks) {
    return null;
  }

  link = document.createElement("a");
  link.id = id;
  link.href = "#";
  link.target = "_blank";
  link.rel = "noopener noreferrer";

  const img = document.createElement("img");
  img.src = iconSrc;
  img.alt = iconAlt;

  const text = document.createElement("span");
  text.textContent = label;

  link.append(img, text);

  const openAll = document.getElementById("openAllApps");
  if (openAll && openAll.parentElement === quickLinks) {
    quickLinks.insertBefore(link, openAll);
  } else {
    quickLinks.appendChild(link);
  }
  return link;
}

function renderVpn(dashboard) {
  const network = dashboard.network || {};
  const services = dashboard.services || {};
  const status = network.status === "on" ? "on" : network.status === "off" ? "off" : "unknown";
  const label = t(`vpn.${status}`);

  setPill(ids.vpnCardPill, status, label);
  ids.vpnWave.classList.remove("on", "off", "unknown");
  ids.vpnWave.classList.add(status);

  ids.vpnReason.textContent = asText(network.reason || network.error, t("status.noStatus"));
  ids.vpnCurrentIp.textContent = asText(network.currentIp);
  ids.vpnOwner.textContent = asText(network.currentOrg, t("status.unavailable"));
  ids.vpnHostIp.textContent = `${t("vpn.hostPrefix")} ${asText(network.hostIp)}`;
  ids.vpnTunnelIp.textContent = `${t("vpn.tunnelPrefix")} ${asText(network.vpnIp)}`;
  ids.vpnProvider.textContent = asText(network.provider, t("status.unavailable"));

  const openRadarr = ensureQuickLink("openRadarr", "Radarr", "./images/radar_logo.png", "Radarr");
  const openSonarr = ensureQuickLink("openSonarr", "Sonarr", "./images/sonarr_logo.png", "Sonarr");
  const openSab = ensureQuickLink("openSab", "SABnzbd", "./images/sab_logo.png", "SABnzbd");
  const openOmbi = ensureQuickLink("openOmbi", "Ombi", "./images/ombi.png", "Ombi");

  if (openRadarr) {
    openRadarr.href = services.radarr?.url || "#";
  }
  if (openSonarr) {
    openSonarr.href = services.sonarr?.url || "#";
  }
  if (openSab) {
    openSab.href = services.sabnzbd?.url || "#";
  }
  if (openOmbi) {
    openOmbi.href = services.ombi?.url || "#";
  }

  if (ids.openAllApps) {
    const openableCount = [openRadarr?.href, openSonarr?.href, openSab?.href, openOmbi?.href]
      .filter((url) => url && url !== "#").length;
    ids.openAllApps.disabled = openableCount === 0;
  }
}

function renderServiceCard(service, cardNode, pillNode, metaNode, kpiNode, essentialNode, serviceType) {
  const online = Boolean(service?.online);
  setCardOnlineState(cardNode, online);
  setPill(pillNode, online ? "online" : "offline", online ? t("status.online") : t("status.offline"));

  if (!online) {
    metaNode.textContent = t("meta.offline", { error: asText(service?.error, t("status.unavailable")) });
    if (serviceType === "radarr") {
      renderMiniKpis(kpiNode, [
        { label: t("kpi.library"), value: "-" },
        { label: t("kpi.wanted"), value: "-" },
        { label: t("kpi.queue"), value: "-" },
        { label: t("kpi.health"), value: "-" },
        { label: t("kpi.diskFree"), value: "-" }
      ]);
      renderEssentialList(essentialNode, []);
    }
    if (serviceType === "sonarr") {
      renderMiniKpis(kpiNode, [
        { label: t("kpi.series"), value: "-" },
        { label: t("kpi.wanted"), value: "-" },
        { label: t("kpi.queue"), value: "-" },
        { label: t("kpi.health"), value: "-" },
        { label: t("kpi.diskFree"), value: "-" }
      ]);
      renderEssentialList(essentialNode, []);
    }
    if (serviceType === "sab") {
      renderMiniKpis(kpiNode, [
        { label: t("kpi.queue"), value: "-" },
        { label: t("kpi.speed"), value: "-" },
        { label: t("kpi.eta"), value: "-" },
        { label: t("kpi.completed"), value: "-" },
        { label: t("kpi.failed"), value: "-" }
      ]);
      renderEssentialList(essentialNode, []);
    }
    return;
  }

  if (serviceType === "radarr") {
    const stats = service.stats || {};
    const queueSummary = service.queueSummary || {};
    const health = service.health || {};
    const disk = service.disk || {};
    const usedPercent = Number(disk.usedPercent);
    metaNode.textContent = t("meta.versionQueueOs", {
      version: asText(service.system?.version),
      queue: asNum(service.queueCount),
      os: asText(service.system?.osName)
    });
    renderMiniKpis(kpiNode, [
      { label: t("kpi.library"), value: asNum(stats.libraryTotal ?? service.libraryCount) },
      { label: t("kpi.wanted"), value: asNum(stats.wanted) },
      { label: t("kpi.downloaded"), value: asNum(stats.downloaded) },
      { label: t("kpi.queue"), value: asNum(service.queueCount) }
    ]);
    renderEssentialList(essentialNode, [
      { label: t("essential.queueDownloading"), value: asNum(queueSummary.downloading) },
      { label: t("essential.queueImporting"), value: asNum(queueSummary.importing) },
      {
        label: t("essential.upcoming7d30d"),
        value: t("value.upcoming", { days7: asNum(stats.upcoming7Days), days30: asNum(stats.upcoming30Days) })
      },
      Number.isFinite(usedPercent)
        ? { label: t("essential.storage"), value: t("value.storageFree", { free: asText(disk.freeReadable) }), progressPercent: usedPercent }
        : { label: t("kpi.diskFree"), value: asText(disk.freeReadable) },
      {
        label: t("essential.healthIssues"),
        value: t("value.healthIssues", { total: asNum(health.totalIssues), warnings: asNum(health.warnings), errors: asNum(health.errors) })
      }
    ]);
    return;
  }

  if (serviceType === "sonarr") {
    const stats = service.stats || {};
    const queueSummary = service.queueSummary || {};
    const health = service.health || {};
    const disk = service.disk || {};
    const usedPercent = Number(disk.usedPercent);
    metaNode.textContent = t("meta.versionQueueOs", {
      version: asText(service.system?.version),
      queue: asNum(service.queueCount),
      os: asText(service.system?.osName)
    });
    renderMiniKpis(kpiNode, [
      { label: t("kpi.series"), value: asNum(stats.libraryTotal ?? service.libraryCount) },
      { label: t("kpi.wanted"), value: asNum(stats.wanted) },
      { label: t("kpi.episodes"), value: asNum(stats.totalEpisodes) },
      { label: t("kpi.queue"), value: asNum(service.queueCount) }
    ]);
    renderEssentialList(essentialNode, [
      {
        label: t("essential.continuingEnded"),
        value: t("value.continuingEnded", { continuing: asNum(stats.continuing), ended: asNum(stats.ended) })
      },
      { label: t("essential.missingEpisodes"), value: asNum(stats.missingEpisodes) },
      { label: t("essential.queueDownloading"), value: asNum(queueSummary.downloading) },
      Number.isFinite(usedPercent)
        ? { label: t("essential.storage"), value: t("value.storageFree", { free: asText(disk.freeReadable) }), progressPercent: usedPercent }
        : { label: t("kpi.diskFree"), value: asText(disk.freeReadable) },
      {
        label: t("essential.healthIssues"),
        value: t("value.healthIssues", { total: asNum(health.totalIssues), warnings: asNum(health.warnings), errors: asNum(health.errors) })
      }
    ]);
    return;
  }

  const stats = service.stats || {};
  const transfer = service.transferStats || {};
  metaNode.textContent = t("meta.versionSystemState", {
    version: asText(service.system?.version),
    status: asText(service.system?.status),
    state: service.system?.paused ? t("status.paused") : t("status.running")
  });
  renderMiniKpis(kpiNode, [
    { label: t("kpi.queue"), value: asNum(stats.queueItems ?? service.queueCount) },
    { label: t("kpi.speed"), value: asText(service.system?.speed) },
    { label: t("kpi.eta"), value: asText(service.system?.eta) },
    { label: t("kpi.completed"), value: asNum(stats.completedJobs) }
  ]);
  renderEssentialList(essentialNode, [
    { label: t("essential.queueLeftMb"), value: asNum(stats.queueLeftMb) },
    { label: t("essential.failedJobs"), value: asNum(stats.failedJobs) },
    { label: t("essential.transferDay"), value: asText(transfer.day) },
    { label: t("essential.transferWeek"), value: asText(transfer.week) },
    { label: t("essential.transferMonth"), value: asText(transfer.month) }
  ]);
}

function renderOmbiCard(service) {
  const online = Boolean(service?.online);
  setCardOnlineState(ids.ombiCard, online);
  setPill(ids.ombiPill, online ? "online" : "offline", online ? t("status.online") : t("status.offline"));

  if (!online) {
    ids.ombiMeta.textContent = t("meta.offline", { error: asText(service?.error, t("status.unavailable")) });
    renderMiniKpis(ids.ombiKpis, [
      { label: t("kpi.requests"), value: "-" },
      { label: t("kpi.pending"), value: "-" },
      { label: t("kpi.approved"), value: "-" },
      { label: t("kpi.available"), value: "-" },
      { label: t("kpi.api"), value: "-" }
    ]);
    renderEssentialList(ids.ombiEssential, []);
    return;
  }

  const stats = service.stats || {};
  const system = service.system || {};
  const apiStatus = system.statusOk ? t("api.healthy") : t("api.unknown");
  ids.ombiMeta.textContent = t("meta.ombi", {
    version: asText(system.version),
    framework: asText(system.frameworkDescription),
    api: apiStatus
  });

  renderMiniKpis(ids.ombiKpis, [
    { label: t("kpi.requests"), value: asNum(stats.total) },
    { label: t("kpi.pending"), value: asNum(stats.pending) },
    { label: t("kpi.approved"), value: asNum(stats.approved) },
    { label: t("kpi.available"), value: asNum(stats.available) },
    { label: t("kpi.api"), value: system.statusOk ? "OK" : "?" }
  ]);

  const detailItems = [
    { label: t("kpi.api"), value: apiStatus },
    { label: t("essential.branch"), value: asText(system.branch) },
    { label: t("essential.database"), value: asText(system.ombiDatabaseType) },
    { label: t("essential.storagePath"), value: asText(system.storagePath) },
    { label: t("essential.os"), value: asText(system.osDescription) }
  ];
  renderEssentialList(ids.ombiEssential, detailItems);
}

function translateContainerState(rawState) {
  const stateText = asText(rawState, "unknown").toLowerCase();
  const key = `container.state.${stateText}`;
  const translated = t(key);
  return translated === key ? stateText : translated;
}

function translateContainerHealth(rawHealth) {
  const healthText = asText(rawHealth, "").toLowerCase();
  if (!healthText || healthText === "-") {
    return "-";
  }
  const key = `container.health.${healthText}`;
  const translated = t(key);
  return translated === key ? healthText : translated;
}

function renderContainerControls(admin) {
  clearNode(ids.containerRows);

  const containersPayload = admin?.containers || {};
  const containers = containersPayload.containers || {};
  const order = ["gluetun", "sabnzbd", "sonarr", "radarr", "ombi", "dashboard"];

  if (!containersPayload.ok) {
    ids.containerRows.appendChild(row(["docker", containersPayload.error || t("container.dockerUnavailable"), "-", "-"]));
    return;
  }

  order.forEach((serviceName) => {
    const info = containers[serviceName] || {};
    const rawState = info.exists ? asText(info.status, "unknown").toLowerCase() : "missing";
    const stateLabel = translateContainerState(rawState);
    const healthLabel = translateContainerHealth(info.health);
    const running = Boolean(info.running);
    const stoppedLike = !running || rawState === "exited" || rawState === "dead" || rawState === "stopped" || rawState === "missing";

    const statusBadge = document.createElement("span");
    statusBadge.className = "status-badge";
    if (running && rawState === "running") {
      statusBadge.classList.add("running");
    } else if (rawState === "exited" || rawState === "dead" || rawState === "stopped" || rawState === "missing") {
      statusBadge.classList.add("stopped");
    } else {
      statusBadge.classList.add("other");
    }
    statusBadge.textContent = stateLabel;

    const actionCell = document.createElement("div");
    actionCell.className = "action-buttons";

    const actions = stoppedLike
      ? ["start"]
      : (serviceName === "gluetun" ? ["restart"] : ["stop", "restart"]);
    actions.forEach((action) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = t(`action.${action}`);
      btn.dataset.service = serviceName;
      btn.dataset.action = action;
      btn.disabled = state.actionInFlight || !info.exists;
      actionCell.appendChild(btn);
    });

    ids.containerRows.appendChild(row([serviceName, statusBadge, healthLabel, actionCell]));
  });
}

function renderAdmin(admin) {
  renderContainerControls(admin);
  const sab = admin?.settings?.sabnzbd;
  if (sab?.online) {
    const paths = sab.paths || {};
    ids.sabDownloadDirInput.value = asText(paths.downloadDir, "");
    ids.sabCompleteDirInput.value = asText(paths.completeDir, "");
  }
}

function renderDashboard(dashboard) {
  renderSummary(dashboard);
  renderVpn(dashboard);

  const services = dashboard.services || {};
  renderServiceCard(services.radarr, ids.radarrCard, ids.radarrPill, ids.radarrMeta, ids.radarrKpis, ids.radarrEssential, "radarr");
  renderServiceCard(services.sonarr, ids.sonarrCard, ids.sonarrPill, ids.sonarrMeta, ids.sonarrKpis, ids.sonarrEssential, "sonarr");
  renderServiceCard(services.sabnzbd, ids.sabCard, ids.sabPill, ids.sabMeta, ids.sabKpis, ids.sabEssential, "sab");
  renderSabLiveQueue(services.sabnzbd, dashboard.generatedAt);
  renderOmbiCard(services.ombi || { online: false, error: t("status.unavailable") });

  ids.lastUpdated.textContent = t("status.updated", { time: toLocalTime(dashboard.generatedAt) });
}

async function refreshDashboard() {
  const payload = await apiGet("/api/dashboard");
  state.dashboard = payload;
  renderDashboard(payload);
}

async function refreshAdmin() {
  const payload = await apiGet("/api/admin");
  state.admin = payload;
  renderAdmin(payload);
}

async function refreshSabLive() {
  try {
    const payload = await apiGet("/api/sab");
    renderSabLiveQueue(payload.sabnzbd || { online: false, error: t("status.unavailable") }, payload.generatedAt);
  } catch (error) {
    renderSabLiveQueue({ online: false, error: error.message });
  }
}

async function withAction(task, successMessage) {
  try {
    state.actionInFlight = true;
    renderAdmin(state.admin || {});
    await task();
    showToast(successMessage);
    await Promise.all([refreshAdmin(), refreshDashboard()]);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    state.actionInFlight = false;
    renderAdmin(state.admin || {});
  }
}

ids.containerRows.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-service][data-action]");
  if (!button) {
    return;
  }
  const serviceName = button.dataset.service;
  const action = button.dataset.action;

  withAction(
    () => apiPost("/api/manage/container", { service: serviceName, action }),
    t("container.actionTriggered", { service: serviceName, action: t(`action.${action}`) })
  );
});

ids.sabPathsForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const downloadDir = ids.sabDownloadDirInput.value.trim();
  const completeDir = ids.sabCompleteDirInput.value.trim();

  withAction(
    () => apiPost("/api/manage/sab-paths", { downloadDir, completeDir }),
    t("toast.sabPathsUpdated")
  );
});

if (ids.openAllApps) {
  ids.openAllApps.addEventListener("click", () => {
    const openRadarr = document.getElementById("openRadarr");
    const openSonarr = document.getElementById("openSonarr");
    const openSab = document.getElementById("openSab");
    const openOmbi = document.getElementById("openOmbi");
    const targets = [openRadarr?.href, openSonarr?.href, openSab?.href, openOmbi?.href]
      .filter((url) => url && url !== "#");
    if (targets.length === 0) {
      showToast(t("toast.noServiceTabs"), true);
      return;
    }

    let opened = 0;
    targets.forEach((url) => {
      const popup = window.open(url, "_blank", "noopener,noreferrer");
      if (popup) {
        popup.blur();
        opened += 1;
      }
    });
    window.focus();
    if (opened === 0) {
      showToast(t("toast.popupBlocked"), true);
      return;
    }
    showToast(t("toast.openedTabs", { count: opened, suffix: opened === 1 ? "" : "s" }));
  });
}

function bindSilentExternalLinks() {
  const links = Array.from(document.querySelectorAll('a[target="_blank"]'));
  links.forEach((link) => {
    if (link.dataset.silentBound === "1") {
      return;
    }
    link.dataset.silentBound = "1";
    link.addEventListener("click", (event) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") {
        return;
      }
      event.preventDefault();
      const popup = window.open(href, "_blank", "noopener,noreferrer");
      if (popup) {
        popup.blur();
      }
      window.focus();
    });
  });
}

async function bootstrap() {
  try {
    const settingsStatus = await apiGet("/api/settings");
    setLanguage(settingsStatus.settings?.language || state.language, true);
    setTheme(settingsStatus.settings?.theme || state.theme, true);
    await Promise.all([refreshDashboard(), refreshAdmin()]);
    await refreshSabLive();
  } catch (error) {
    showToast(t("error.initialLoad", { error: error.message }), true);
  }

  setInterval(() => {
    refreshDashboard().catch((error) => showToast(t("error.refreshDashboard", { error: error.message }), true));
  }, DASH_REFRESH_MS);

  setInterval(() => {
    refreshAdmin().catch((error) => showToast(t("error.refreshAdmin", { error: error.message }), true));
  }, ADMIN_REFRESH_MS);

  setInterval(() => {
    refreshSabLive();
  }, SAB_REFRESH_MS);

  bindSilentExternalLinks();
}

if (ids.languageSelect) {
  ids.languageSelect.addEventListener("change", (event) => {
    setLanguage(event.target.value, true);
  });
}

themeOptions.forEach((button) => {
  button.addEventListener("click", () => {
    setTheme(button.dataset.themeChoice, true);
  });
});

setLanguage(state.language, false);
setTheme(state.theme, false);
bootstrap();
