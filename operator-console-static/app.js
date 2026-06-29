(function () {
  "use strict";

  var DEFAULT_API_BASE = "http://localhost:8080";
  var SENSITIVE_KEYS = [
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "password",
    "token",
    "api_key",
    "secret",
    "private_key",
    "credential",
    "authorization",
    "bearer"
  ];
  var VIEW_DEMOS = {
    overview: "demo-data/overview-view-model.json",
    readiness: "demo-data/release-readiness-view-model.json",
    release_candidate: "demo-data/release-readiness-view-model.json",
    module_lifecycle: "demo-data/module-lifecycle-dashboard.json",
    model_provider_hardening: "demo-data/provider-hardening-view-model.json",
    operator_actions: "demo-data/operator-action-preview.json",
    incidents: "demo-data/incidents-view-model.json",
    registry_integrity: "demo-data/settings-safety-view-model.json",
    settings_safety: "demo-data/settings-safety-view-model.json",
    audit_provenance: "demo-data/settings-safety-view-model.json"
  };
  var VIEW_GROUPS = {
    platform: ["overview", "readiness", "release_candidate"],
    modules: ["module_lifecycle"],
    providers: ["model_provider_hardening"],
    actions: ["operator_actions"],
    auth: ["overview"],
    evidence: ["registry_integrity", "audit_provenance"],
    safety: ["settings_safety", "incidents"]
  };
  var SAFE_COPY_COMMANDS = [
    "./scripts/ui-release-gate.sh",
    "./scripts/static-console-safety-check.sh",
    "./scripts/operator-platform-regression.sh",
    "./scripts/operator-platform-freeze-gate.sh",
    "./scripts/docs-check.sh"
  ];
  var MODULE_LIFECYCLE_DEMOS = {
    generic_knowledge_trail: "demo-data/generic-knowledge-trail.json",
    module_activation_blockers: "demo-data/module-activation-blockers.json",
    module_mock_runtime_trail: "demo-data/module-mock-runtime-trail.json",
    module_review_checklist: "demo-data/module-review-checklist.json"
  };
  var OPERATOR_ACTION_DEMOS = {
    preview: "demo-data/operator-action-preview.json",
    blockers: "demo-data/operator-action-blockers.json",
    review: "demo-data/operator-action-review.json"
  };
  var ACTION_AUTHORIZATION_DEMOS = {
    preview: "demo-data/action-authorization-preview.json",
    deny_matrix: "demo-data/action-authorization-deny-matrix.json"
  };
  var AUTH_RUNTIME_DEMOS = {
    status: "demo-data/auth-runtime-status.json",
    preview: "demo-data/mock-claims-preview.json"
  };
  var CONNECTOR_RUNTIME_DEMOS = {
    status: "demo-data/connector-runtime-status.json",
    preview: "demo-data/connector-boundary-preview.json"
  };
  var LOCAL_AUTH_DEMOS = {
    status: "demo-data/local-auth-status.json",
    role_filter: "demo-data/role-filtered-view-model.json"
  };
  var LOCAL_SESSION_DEMOS = {
    status: "demo-data/local-session-status.json",
    preview: "demo-data/local-session-preview.json"
  };
  var ROLE_ACCESS_DEMOS = {
    matrix: "demo-data/role-access-matrix.json",
    viewer: "demo-data/role-viewer-dashboard.json",
    operator: "demo-data/role-operator-dashboard.json",
    reviewer: "demo-data/role-reviewer-dashboard.json",
    admin: "demo-data/role-admin-dashboard.json",
    auditor: "demo-data/role-auditor-dashboard.json"
  };
  var apiConfig = resolveApiBase();
  var state = {
    apiBase: apiConfig.apiBase,
    activeView: "overview",
    activeGroup: "all",
    activeRole: "viewer",
    apiAllowed: apiConfig.apiAllowed
  };

  document.addEventListener("DOMContentLoaded", function () {
    bindGroupTabs();
    bindTabs();
    bindRoleSwitcher();
    bindSectionNavigation();
    bindSafetyBlockers();
    bindCommandCopy();
    loadLocalAuthPanels();
    loadRoleAccessPreview();
    loadLocalSessionPanels();
    loadActionAuthorizationPanel();
    loadAuthRuntimePanel();
    loadConnectorRuntimePanels();
    loadView(state.activeView);
  });

  function resolveApiBase() {
    var params = new URLSearchParams(window.location.search);
    var requested = params.get("api") || DEFAULT_API_BASE;
    if (!isLocalApiOrigin(requested)) {
      return { apiBase: DEFAULT_API_BASE, apiAllowed: false };
    }
    return { apiBase: normalizeOrigin(requested), apiAllowed: true };
  }

  function normalizeOrigin(value) {
    var parsed = new URL(value, window.location.href);
    return parsed.origin;
  }

  function isLocalApiOrigin(value) {
    try {
      var parsed = new URL(value, window.location.href);
      return parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
    } catch (_error) {
      return false;
    }
  }

  function bindTabs() {
    var tabs = document.querySelectorAll(".view-tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setActiveView(tab.getAttribute("data-view") || "overview");
      });
      tab.addEventListener("keydown", function (event) {
        moveTabFocus(event, ".view-tab:not([hidden])");
      });
    });
  }

  function bindGroupTabs() {
    var tabs = document.querySelectorAll(".group-tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setActiveGroup(tab.getAttribute("data-group") || "all");
      });
      tab.addEventListener("keydown", function (event) {
        moveTabFocus(event, ".group-tab");
      });
    });
  }

  function bindRoleSwitcher() {
    var tabs = document.querySelectorAll(".role-tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (item) {
          item.classList.remove("is-active");
          item.setAttribute("aria-pressed", "false");
        });
        tab.classList.add("is-active");
        tab.setAttribute("aria-pressed", "true");
        state.activeRole = tab.getAttribute("data-role") || "viewer";
        loadRoleAccessPreview();
      });
      tab.addEventListener("keydown", function (event) {
        moveTabFocus(event, ".role-tab");
      });
    });
  }

  function bindSectionNavigation() {
    var links = document.querySelectorAll(".section-link[href]");
    links.forEach(function (link) {
      link.addEventListener("click", function () {
        var target = document.querySelector(link.getAttribute("href"));
        if (target && typeof target.focus === "function") {
          window.setTimeout(function () {
            target.focus();
          }, 0);
        }
      });
    });
  }

  function bindSafetyBlockers() {
    var control = document.getElementById("safety-blockers-control");
    if (!control) {
      return;
    }
    control.addEventListener("click", function () {
      setActiveGroup("safety", { keepView: true });
      renderSafetyBlockerView();
      var target = document.getElementById("forbidden-actions");
      if (target && typeof target.focus === "function") {
        target.focus();
      }
    });
  }

  function bindCommandCopy() {
    var buttons = document.querySelectorAll(".copy-command");
    buttons.forEach(function (button) {
      var command = button.getAttribute("data-command") || "";
      if (SAFE_COPY_COMMANDS.indexOf(command) === -1) {
        button.disabled = true;
        button.textContent = "Unavailable";
        return;
      }
      button.addEventListener("click", function () {
        copyLocalCommand(command);
      });
    });
  }

  function setActiveGroup(group, options) {
    var nextGroup = VIEW_GROUPS[group] || group === "all" ? group : "all";
    state.activeGroup = nextGroup;
    document.querySelectorAll(".group-tab").forEach(function (tab) {
      var active = tab.getAttribute("data-group") === nextGroup;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-pressed", active ? "true" : "false");
    });
    filterViewsForGroup(nextGroup);
    if (options && options.keepView) {
      return;
    }
    var firstView = firstViewForGroup(nextGroup);
    if (firstView && firstView !== state.activeView) {
      setActiveView(firstView);
    }
  }

  function filterViewsForGroup(group) {
    document.querySelectorAll(".view-tab").forEach(function (tab) {
      var tabGroup = tab.getAttribute("data-group") || "platform";
      var visible = group === "all" || tabGroup === group;
      tab.hidden = !visible;
      tab.setAttribute("aria-hidden", visible ? "false" : "true");
    });
  }

  function firstViewForGroup(group) {
    if (group === "all") {
      return state.activeView || "overview";
    }
    var views = VIEW_GROUPS[group] || [];
    return views[0] || "overview";
  }

  function setActiveView(view) {
    state.activeView = view;
    document.querySelectorAll(".view-tab").forEach(function (item) {
      var active = item.getAttribute("data-view") === view;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", active ? "true" : "false");
    });
    loadView(state.activeView);
  }

  function moveTabFocus(event, selector) {
    if (["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End"].indexOf(event.key) === -1) {
      return;
    }
    var tabs = Array.prototype.slice.call(document.querySelectorAll(selector));
    var current = tabs.indexOf(event.currentTarget);
    if (current === -1 || !tabs.length) {
      return;
    }
    event.preventDefault();
    var next = current;
    if (event.key === "Home") {
      next = 0;
    } else if (event.key === "End") {
      next = tabs.length - 1;
    } else if (event.key === "ArrowDown" || event.key === "ArrowRight") {
      next = (current + 1) % tabs.length;
    } else {
      next = (current - 1 + tabs.length) % tabs.length;
    }
    tabs[next].focus();
  }

  function copyLocalCommand(command) {
    if (SAFE_COPY_COMMANDS.indexOf(command) === -1) {
      setCopyStatus("Command copy blocked.");
      return;
    }
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
      setCopyStatus("Clipboard unavailable. Use the visible local command text.");
      return;
    }
    navigator.clipboard.writeText(command)
      .then(function () {
        setCopyStatus("Copied local check command.");
      })
      .catch(function () {
        setCopyStatus("Clipboard unavailable. Use the visible local command text.");
      });
  }

  function setCopyStatus(message) {
    var status = document.getElementById("copy-status");
    if (status) {
      status.textContent = message;
    }
  }

  function loadView(view) {
    if (view === "safety_blockers") {
      renderSafetyBlockerView();
      return;
    }
    setStatus("Loading " + labelFor(view) + ".");
    if (!state.apiAllowed) {
      setStatus("Blocked non-local API. Loading offline demo data.");
      loadDemo(view);
      return;
    }
    fetchViewModel(view)
      .then(function (model) {
        setStatus("Loaded read-only data from local AION Brain API.");
        renderView(redact(model));
      })
      .catch(function () {
        setStatus("Local API unavailable. Loading offline demo data.");
        loadDemo(view);
      });
  }

  function fetchViewModel(view) {
    var endpoint = state.apiBase + "/brain/operator-console/view-model";
    return fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        view: view,
        owner_scope: ["workspace:main"],
        include_actions: true,
        include_forbidden_actions: true,
        include_refs: true,
        metadata: { static_prototype: true }
      })
    }).then(function (response) {
      if (!response.ok) {
        throw new Error("view model unavailable");
      }
      return response.json();
    });
  }

  function loadLocalAuthPanels() {
    var statusPromise = state.apiAllowed
      ? fetchLocalAuthStatus().catch(function () {
        return fetchJson(LOCAL_AUTH_DEMOS.status);
      })
      : fetchJson(LOCAL_AUTH_DEMOS.status);
    Promise.all([
      statusPromise,
      fetchJson(LOCAL_AUTH_DEMOS.role_filter)
    ])
      .then(function (payloads) {
        renderLocalAuthStatus(redact(payloads[0]));
        renderLocalAuthRoleFilter(redact(payloads[1]));
      })
      .catch(function () {
        renderLocalAuthStatus({
          production_auth_enabled: false,
          credentials_enabled: false,
          sessions_enabled: false,
          external_identity_provider_enabled: false,
          write_actions_enabled: false,
          no_go_warnings: ["local_auth_demo_unavailable"]
        });
        renderLocalAuthRoleFilter({ roles: [], removed_actions: [] });
      });
  }

  function loadRoleAccessPreview() {
    Promise.all([
      fetchJson(ROLE_ACCESS_DEMOS.matrix),
      fetchJson(ROLE_ACCESS_DEMOS[state.activeRole] || ROLE_ACCESS_DEMOS.viewer)
    ])
      .then(function (payloads) {
        renderRoleAccessPreview(redact(payloads[0]), redact(payloads[1]));
      })
      .catch(function () {
        renderRoleAccessPreview(
          {
            static_console_roles: ["viewer", "operator", "reviewer", "admin", "auditor"],
            system_service_exposed_in_static_console: false
          },
          {
            role: state.activeRole,
            visible_views: [],
            removed_sections: [],
            removed_actions: [],
            forbidden_actions_visible: true,
            write_allowed: false,
            execute_allowed: false,
            activation_allowed: false,
            external_calls_allowed: false
          }
        );
      });
  }

  function fetchLocalAuthStatus() {
    var endpoint = state.apiBase + "/brain/local-auth/status?scope=workspace:main";
    return fetch(endpoint).then(function (response) {
      if (!response.ok) {
        throw new Error("local auth status unavailable");
      }
      return response.json();
    });
  }

  function loadDemo(view) {
    if (view === "module_lifecycle") {
      loadModuleLifecycleDemo();
      return;
    }
    if (view === "operator_actions") {
      loadOperatorActionsDemo();
      return;
    }
    var demoPath = VIEW_DEMOS[view] || VIEW_DEMOS.overview;
    fetchJson(demoPath)
      .then(function (model) {
        renderView(redact(model));
      })
      .catch(function () {
        renderUnavailable(view);
      });
  }

  function loadModuleLifecycleDemo() {
    Promise.all([
      fetchJson(VIEW_DEMOS.module_lifecycle),
      fetchJson(MODULE_LIFECYCLE_DEMOS.generic_knowledge_trail),
      fetchJson(MODULE_LIFECYCLE_DEMOS.module_activation_blockers),
      fetchJson(MODULE_LIFECYCLE_DEMOS.module_mock_runtime_trail),
      fetchJson(MODULE_LIFECYCLE_DEMOS.module_review_checklist)
    ])
      .then(function (payloads) {
        var model = payloads[0];
        model.generic_knowledge_trail = payloads[1];
        model.module_activation_blockers = payloads[2];
        model.module_mock_runtime_trail = payloads[3];
        model.module_review_checklist = payloads[4];
        renderView(redact(model));
      })
      .catch(function () {
        renderUnavailable("module_lifecycle");
      });
  }

  function loadOperatorActionsDemo() {
    Promise.all([
      fetchJson(OPERATOR_ACTION_DEMOS.preview),
      fetchJson(OPERATOR_ACTION_DEMOS.blockers),
      fetchJson(OPERATOR_ACTION_DEMOS.review)
    ])
      .then(function (payloads) {
        var model = payloads[0];
        model.operator_action_blockers = payloads[1];
        model.operator_action_review = payloads[2];
        renderView(redact(model));
      })
      .catch(function () {
        renderUnavailable("operator_actions");
      });
  }

  function loadActionAuthorizationPanel() {
    Promise.all([
      fetchJson(ACTION_AUTHORIZATION_DEMOS.preview),
      fetchJson(ACTION_AUTHORIZATION_DEMOS.deny_matrix)
    ])
      .then(function (payloads) {
        renderActionAuthorizationPanel(redact(payloads[0]), redact(payloads[1]));
      })
      .catch(function () {
        renderActionAuthorizationPanel(
          {
            decision: "unavailable",
            policy_allowed: false,
            role_allowed: false,
            session_allowed: false,
            dry_run_only: true,
            write_allowed: false,
            execution_allowed: false,
            activation_allowed: false,
            external_calls_allowed: false
          },
          { denials: [] }
        );
      });
  }

  function fetchJson(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) {
        throw new Error("demo unavailable");
      }
      return response.json();
    });
  }

  function redact(value) {
    if (Array.isArray(value)) {
      return value.map(redact);
    }
    if (value && typeof value === "object") {
      return Object.keys(value).reduce(function (result, key) {
        if (isSensitiveKey(key)) {
          result[key] = "[redacted]";
        } else {
          result[key] = redact(value[key]);
        }
        return result;
      }, {});
    }
    if (typeof value === "string" && looksSensitive(value)) {
      return "[redacted]";
    }
    return value;
  }

  function isSensitiveKey(key) {
    var normalized = key.toLowerCase().replace(/-/g, "_");
    if ([
      "token_issued",
      "token_present",
      "token_issuance_enabled",
      "cookie_issued",
      "cookie_present",
      "cookie_issuance_enabled",
      "credential_backed",
      "credentials_present",
      "credentials_enabled",
      "tokens_enabled",
      "cookies_enabled",
      "session_persisted",
      "session_persistence_enabled",
      "production_auth_enabled",
      "auth_runtime_enabled",
      "external_identity_provider_enabled",
      "login_endpoint_enabled",
      "logout_endpoint_enabled",
      "mock_claims_preview_enabled",
      "actor_mapping_preview_enabled",
      "connector_runtime_enabled",
      "connector_mock_preview_enabled",
      "connector_egress_preview_enabled",
      "connector_ingress_preview_enabled",
      "connector_external_calls_enabled",
      "connector_credentials_enabled",
      "connector_token_storage_enabled",
      "connector_activation_enabled",
      "connector_route_registration_enabled"
    ].indexOf(normalized) !== -1) {
      return false;
    }
    return SENSITIVE_KEYS.some(function (part) {
      return normalized.indexOf(part) !== -1;
    });
  }

  function looksSensitive(value) {
    var normalized = value.toLowerCase();
    return normalized.indexOf("sk-") !== -1 ||
      normalized.indexOf("ghp_") !== -1 ||
      normalized.indexOf("xoxb-") !== -1;
  }

  function renderView(model) {
    document.getElementById("view-title").textContent = model.title || labelFor(model.view);
    document.getElementById("view-status").textContent = safeText(model.status || "unknown");
    document.getElementById("view-summary").textContent = safeText(model.summary || "");
    renderSections(Array.isArray(model.sections) ? model.sections : []);
    renderForbiddenActions(
      Array.isArray(model.forbidden_actions) ? model.forbidden_actions : collectActions(model)
    );
    renderModuleLifecycleDashboard(model);
    renderOperatorActionsPanel(model);
  }

  function renderUnavailable(view) {
    renderView({
      view: view,
      title: labelFor(view),
      status: "unavailable",
      summary: "Offline demo data could not be loaded. No action was performed.",
      sections: [
        {
          title: "Unavailable",
          status: "unavailable",
          summary: "Static prototype rendered a safe unavailable state.",
          blockers: [{ message: "local data unavailable" }],
          warnings: [],
          refs: []
        }
      ],
      forbidden_actions: forbiddenFallback()
    });
  }

  function renderSafetyBlockerView() {
    setStatus("Showing static safety blockers. No action was performed.");
    renderView({
      view: "safety_blockers",
      title: "Safety Blockers",
      status: "blocked",
      summary: "Read-only no-go controls and forbidden descriptors are visible for review.",
      sections: [
        {
          title: "Static Console Boundary",
          status: "blocked",
          severity: "release blocker",
          summary: "Any write, activation, execution, provider call, login, credential input, or external call remains blocked.",
          blockers: [
            { message: "write controls remain absent" },
            { message: "activation controls remain absent" },
            { message: "execution controls remain absent" },
            { message: "provider call controls remain absent" }
          ],
          warnings: [
            "safe command copy is limited to local verification commands"
          ],
          refs: [
            "docs/operator-console/static-console-safety-review.md",
            "docs/operator-console/static-console-ux-refinement.md"
          ]
        },
        {
          title: "Auth and Session Boundary",
          status: "blocked",
          severity: "release blocker",
          summary: "Production auth, login, protected material input, browser storage, and persistent sessions remain unavailable.",
          blockers: [
            { message: "production auth remains disabled" },
            { message: "login and logout controls remain absent" },
            { message: "browser storage remains unused" }
          ],
          warnings: [],
          refs: [
            "docs/operator-console/static-console-accessibility-checklist.md"
          ]
        }
      ],
      forbidden_actions: forbiddenFallback()
    });
  }

  function renderSections(sections) {
    var container = document.getElementById("sections");
    container.textContent = "";
    sections.forEach(function (section) {
      var card = document.createElement("article");
      card.className = "section-card";
      var title = document.createElement("h3");
      title.textContent = safeText(section.title || section.section_key || "Section");
      var summary = document.createElement("p");
      summary.textContent = safeText(section.summary || "");
      var meta = document.createElement("div");
      meta.className = "meta-row";
      meta.appendChild(pill(section.status || "unknown"));
      meta.appendChild(pill(section.severity || "info"));
      card.appendChild(title);
      card.appendChild(summary);
      card.appendChild(meta);
      card.appendChild(listBlock("Blockers", section.blockers || []));
      card.appendChild(listBlock("Warnings", section.warnings || []));
      card.appendChild(listBlock("Refs", section.refs || []));
      container.appendChild(card);
    });
  }

  function renderModuleLifecycleDashboard(model) {
    var isModuleView = model && model.view === "module_lifecycle";
    var dashboard = document.getElementById("module-dashboard");
    if (!dashboard) {
      return;
    }
    dashboard.classList.toggle("is-muted", !isModuleView);
    document.getElementById("module-dashboard-summary").textContent = isModuleView
      ? safeText(model.summary || "Read-only module lifecycle evidence is visible.")
      : "Select Module Lifecycle to inspect the Generic Knowledge Intelligence trail.";
    renderSafetyLabels(isModuleView ? model.safety_labels || model : defaultSafetyLabels());
    renderLifecycleStages(isModuleView && Array.isArray(model.stages) ? model.stages : []);
    renderCapabilityTrail(isModuleView ? model.generic_knowledge_trail : null);
    renderBlockers(isModuleView ? lifecycleBlockers(model) : []);
    renderMockRuntimeTrail(isModuleView ? model.module_mock_runtime_trail : null);
    renderReviewChecklist(isModuleView ? model.module_review_checklist : null);
  }

  function defaultSafetyLabels() {
    return {
      activation_allowed: false,
      execution_allowed: false,
      registration_allowed: false,
      code_loaded: false,
      external_calls_made: false
    };
  }

  function renderSafetyLabels(labels) {
    var container = document.getElementById("module-safety-labels");
    container.textContent = "";
    [
      "activation_allowed",
      "execution_allowed",
      "registration_allowed",
      "code_loaded",
      "external_calls_made"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      var label = document.createElement("span");
      label.textContent = key + "=" + String(Boolean(labels && labels[key]));
      card.appendChild(label);
      container.appendChild(card);
    });
  }

  function renderLifecycleStages(stages) {
    var container = document.getElementById("module-lifecycle-stages");
    container.textContent = "";
    if (!stages.length) {
      container.appendChild(emptyNote("Module lifecycle stages render here."));
      return;
    }
    stages.forEach(function (stage, index) {
      var card = document.createElement("article");
      card.className = "lifecycle-stage";
      var indexNode = document.createElement("span");
      indexNode.className = "stage-index";
      indexNode.textContent = String(index + 1).padStart(2, "0");
      var title = document.createElement("h4");
      title.textContent = safeText(stage.title || stage.stage_key || "Lifecycle stage");
      var meta = document.createElement("div");
      meta.className = "meta-row";
      meta.appendChild(pill(stage.status || "unknown"));
      card.appendChild(indexNode);
      card.appendChild(title);
      card.appendChild(meta);
      card.appendChild(listBlock("Evidence", stage.evidence_refs || []));
      card.appendChild(listBlock("Blockers", stage.blockers || []));
      card.appendChild(listBlock("Warnings", stage.warnings || []));
      card.appendChild(listBlock("Allowed descriptors", stage.allowed_actions || []));
      card.appendChild(listBlock("Forbidden descriptors", stage.forbidden_actions || []));
      container.appendChild(card);
    });
  }

  function renderCapabilityTrail(trail) {
    var container = document.getElementById("module-capability-trail");
    container.textContent = "";
    var capabilities = trail && Array.isArray(trail.capabilities) ? trail.capabilities : [];
    if (!capabilities.length) {
      container.appendChild(emptyNote("Generic capability metadata renders here."));
      return;
    }
    capabilities.forEach(function (capability) {
      var card = document.createElement("article");
      card.className = "capability-card";
      var title = document.createElement("h4");
      title.textContent = safeText(capability.capability_key);
      var label = document.createElement("p");
      label.textContent = safeText(capability.label || "Generic capability");
      var meta = document.createElement("div");
      meta.className = "meta-row";
      meta.appendChild(pill("dry_run_supported=" + String(Boolean(capability.dry_run_supported))));
      meta.appendChild(pill("controlled_supported=" + String(Boolean(capability.controlled_supported))));
      meta.appendChild(pill("activation_allowed=" + String(Boolean(capability.activation_allowed))));
      card.appendChild(title);
      card.appendChild(label);
      card.appendChild(meta);
      card.appendChild(listBlock("Evidence", capability.evidence_refs || []));
      container.appendChild(card);
    });
  }

  function renderBlockers(blockers) {
    var container = document.getElementById("module-blockers");
    container.textContent = "";
    if (!blockers.length) {
      container.appendChild(emptyNote("Expected blockers render here."));
      return;
    }
    blockers.forEach(function (blocker) {
      var card = document.createElement("div");
      card.className = "blocker-badge";
      var key = document.createElement("strong");
      key.textContent = safeText(blocker.blocker_key || "blocker");
      var message = document.createElement("span");
      message.textContent = safeText(blocker.message || "Blocked by design.");
      var bypass = document.createElement("small");
      bypass.textContent = "bypassable=" + String(Boolean(blocker.bypassable));
      card.appendChild(key);
      card.appendChild(message);
      card.appendChild(bypass);
      container.appendChild(card);
    });
  }

  function renderMockRuntimeTrail(trail) {
    var container = document.getElementById("module-mock-runtime");
    container.textContent = "";
    var runs = trail && Array.isArray(trail.mock_runs) ? trail.mock_runs : [];
    if (!runs.length) {
      container.appendChild(emptyNote("Synthetic mock runtime output renders here."));
      return;
    }
    runs.forEach(function (run) {
      var card = document.createElement("article");
      card.className = "mock-run-card";
      var title = document.createElement("h4");
      title.textContent = safeText(run.mock_run_id || "mock run");
      var summary = document.createElement("p");
      summary.textContent = safeText(run.output_summary || "Synthetic output.");
      var meta = document.createElement("div");
      meta.className = "meta-row";
      meta.appendChild(pill("synthetic=" + String(Boolean(run.synthetic))));
      meta.appendChild(pill("confidence=" + String(run.confidence || "n/a")));
      meta.appendChild(pill("external_calls_made=" + String(Boolean(run.external_calls_made))));
      card.appendChild(title);
      card.appendChild(summary);
      card.appendChild(meta);
      container.appendChild(card);
    });
  }

  function renderReviewChecklist(panel) {
    var container = document.getElementById("module-review-checklist");
    container.textContent = "";
    var checklist = panel && Array.isArray(panel.checklist) ? panel.checklist : [];
    if (!checklist.length) {
      container.appendChild(emptyNote("Operator review checklist renders here."));
      return;
    }
    checklist.forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = safeText(item.label || item.check_key || "review item");
      var status = document.createElement("strong");
      status.textContent = safeText(item.status || "unknown");
      row.appendChild(label);
      row.appendChild(status);
      container.appendChild(row);
    });
  }

  function renderOperatorActionsPanel(model) {
    var isOperatorActionView = model && model.view === "operator_actions";
    var panel = document.getElementById("operator-actions-panel");
    if (!panel) {
      return;
    }
    panel.classList.toggle("is-muted", !isOperatorActionView);
    document.getElementById("operator-actions-summary").textContent = isOperatorActionView
      ? safeText(model.summary || "Dry-run operator action preview is visible.")
      : "Select Operator Actions to inspect dry-run request records.";
    renderOperatorActionSafety(isOperatorActionView ? model : defaultOperatorActionSafety());
    renderOperatorActionEffects(
      "operator-action-effects",
      isOperatorActionView && Array.isArray(model.expected_effects) ? model.expected_effects : [],
      "Expected effects render here."
    );
    renderOperatorActionEffects(
      "operator-action-blocked-effects",
      isOperatorActionView && Array.isArray(model.blocked_effects) ? model.blocked_effects : [],
      "Blocked effects render here."
    );
    renderOperatorActionBlockers(isOperatorActionView ? operatorActionBlockers(model) : []);
    renderOperatorActionReview(isOperatorActionView ? model.operator_action_review || model : null);
  }

  function defaultOperatorActionSafety() {
    return {
      execution_allowed: false,
      external_calls_allowed: false,
      activation_allowed: false,
      would_execute: false
    };
  }

  function renderOperatorActionSafety(labels) {
    var container = document.getElementById("operator-action-safety");
    container.textContent = "";
    [
      "execution_allowed",
      "external_calls_allowed",
      "activation_allowed",
      "would_execute"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(labels && labels[key]));
      container.appendChild(card);
    });
  }

  function renderOperatorActionEffects(containerId, effects, emptyMessage) {
    var container = document.getElementById(containerId);
    container.textContent = "";
    if (!effects.length) {
      container.appendChild(emptyNote(emptyMessage));
      return;
    }
    effects.forEach(function (effect) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = safeText(effect.effect || "effect");
      var status = document.createElement("strong");
      status.textContent = safeText(
        effect.blocked ? "blocked" : "would_execute=" + String(Boolean(effect.would_execute))
      );
      row.appendChild(label);
      row.appendChild(status);
      container.appendChild(row);
    });
  }

  function renderOperatorActionBlockers(blockers) {
    var container = document.getElementById("operator-action-blockers");
    container.textContent = "";
    if (!blockers.length) {
      container.appendChild(emptyNote("Operator action blockers render here."));
      return;
    }
    blockers.forEach(function (blocker) {
      var card = document.createElement("div");
      card.className = "blocker-badge";
      var key = document.createElement("strong");
      key.textContent = safeText(blocker.blocker_key || blocker.blocker_type || "blocker");
      var message = document.createElement("span");
      message.textContent = safeText(blocker.message || blocker.reason || "Blocked by design.");
      var bypass = document.createElement("small");
      bypass.textContent = "bypassable=" + String(Boolean(blocker.bypassable));
      card.appendChild(key);
      card.appendChild(message);
      card.appendChild(bypass);
      container.appendChild(card);
    });
  }

  function renderOperatorActionReview(panel) {
    var container = document.getElementById("operator-action-review");
    container.textContent = "";
    var review = panel && panel.review ? panel.review : panel;
    if (!review || !review.decision) {
      container.appendChild(emptyNote("Operator action review records render here."));
      return;
    }
    [
      ["decision", review.decision],
      ["approval_present", String(Boolean(review.approval_present))],
      ["execution_allowed", String(Boolean(review.execution_allowed))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1]);
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function renderActionAuthorizationPanel(preview, denyMatrix) {
    renderActionAuthorizationSafety(preview);
    renderActionAuthorizationDecision(preview);
    renderActionAuthorizationDenials(denyMatrix);
  }

  function renderActionAuthorizationSafety(preview) {
    var grid = document.getElementById("action-authz-safety");
    if (!grid) {
      return;
    }
    grid.textContent = "";
    [
      "dry_run_only",
      "write_allowed",
      "execution_allowed",
      "activation_allowed",
      "external_calls_allowed"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(preview && preview[key]));
      grid.appendChild(card);
    });
  }

  function renderActionAuthorizationDecision(preview) {
    var container = document.getElementById("action-authz-decision");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["decision", preview.decision || "deny"],
      ["status", preview.status || "blocked"],
      ["role_allowed", String(Boolean(preview.role_allowed))],
      ["policy_allowed", String(Boolean(preview.policy_allowed))],
      ["session_allowed", String(Boolean(preview.session_allowed))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1]);
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function renderActionAuthorizationDenials(matrix) {
    var container = document.getElementById("action-authz-deny-matrix");
    if (!container) {
      return;
    }
    container.textContent = "";
    var denials = matrix && Array.isArray(matrix.denials) ? matrix.denials : [];
    if (!denials.length) {
      container.appendChild(emptyNote("Authorization denials render here."));
      return;
    }
    denials.forEach(function (denial) {
      var card = document.createElement("div");
      card.className = "blocker-badge";
      var role = document.createElement("strong");
      role.textContent = safeText(denial.role || denial.reason || "denied");
      var reason = document.createElement("span");
      reason.textContent = safeText(denial.reason || "blocked by dry-run boundary");
      card.appendChild(role);
      card.appendChild(reason);
      container.appendChild(card);
    });
  }

  function renderLocalAuthStatus(status) {
    var grid = document.getElementById("local-auth-status-grid");
    var warnings = document.getElementById("local-auth-warnings");
    if (!grid || !warnings) {
      return;
    }
    grid.textContent = "";
    [
      "production_auth_enabled",
      "credentials_enabled",
      "sessions_enabled",
      "external_identity_provider_enabled",
      "write_actions_enabled"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(status && status[key]));
      grid.appendChild(card);
    });
    warnings.textContent = "";
    var items = status && Array.isArray(status.no_go_warnings) ? status.no_go_warnings : [];
    if (!items.length) {
      warnings.appendChild(emptyNote("No-go warnings render here."));
      return;
    }
    items.forEach(function (item) {
      var badge = document.createElement("div");
      badge.className = "blocker-badge";
      var label = document.createElement("strong");
      label.textContent = safeText(item);
      var value = document.createElement("span");
      value.textContent = "blocked by design";
      badge.appendChild(label);
      badge.appendChild(value);
      warnings.appendChild(badge);
    });
  }

  function renderLocalAuthRoleFilter(model) {
    var container = document.getElementById("local-auth-role-filter");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["roles", Array.isArray(model.roles) ? model.roles.join(", ") : "viewer"],
      [
        "removed_actions",
        Array.isArray(model.removed_actions) ? model.removed_actions.join(", ") : ""
      ],
      ["read_only", String(Boolean(model.read_only !== false))],
      ["redaction_applied", String(Boolean(model.redaction_applied !== false))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1] || "none");
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function renderRoleAccessPreview(matrix, preview) {
    renderRoleSafety(preview);
    renderRoleVisibleViews(preview);
    renderRoleFilteredSurface(preview);
    renderRoleForbiddenVisibility(matrix, preview);
  }

  function renderRoleSafety(preview) {
    var grid = document.getElementById("role-access-safety");
    if (!grid) {
      return;
    }
    grid.textContent = "";
    [
      "write_allowed",
      "execute_allowed",
      "activation_allowed",
      "external_calls_allowed"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(preview && preview[key]));
      grid.appendChild(card);
    });
  }

  function renderRoleVisibleViews(preview) {
    var container = document.getElementById("role-visible-views");
    if (!container) {
      return;
    }
    container.textContent = "";
    var views = preview && Array.isArray(preview.visible_views) ? preview.visible_views : [];
    if (!views.length) {
      container.appendChild(emptyNote("Visible views render here."));
      return;
    }
    views.forEach(function (view) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = safeText(view);
      var value = document.createElement("strong");
      value.textContent = "read-only";
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function renderRoleFilteredSurface(preview) {
    var container = document.getElementById("role-filtered-surface");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["role", preview.role || state.activeRole],
      [
        "removed_sections",
        Array.isArray(preview.removed_sections) ? preview.removed_sections.join(", ") : "none"
      ],
      [
        "removed_actions",
        Array.isArray(preview.removed_actions) ? preview.removed_actions.join(", ") : "none"
      ],
      ["redaction_applied", String(Boolean(preview.redaction_applied !== false))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1] || "none");
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function renderRoleForbiddenVisibility(matrix, preview) {
    var container = document.getElementById("role-forbidden-visibility");
    if (!container) {
      return;
    }
    container.textContent = "";
    var visible = preview && preview.forbidden_actions_visible === true;
    var roles = matrix && Array.isArray(matrix.static_console_roles)
      ? matrix.static_console_roles
      : ["viewer", "operator", "reviewer", "admin", "auditor"];
    [
      ["forbidden_actions_visible", String(visible)],
      [
        "static_roles",
        roles.filter(function (role) {
          return role !== "system_service";
        }).join(", ")
      ],
      [
        "system_service_exposed",
        String(Boolean(matrix && matrix.system_service_exposed_in_static_console))
      ]
    ].forEach(function (item) {
      var badge = document.createElement("div");
      badge.className = "blocker-badge";
      var label = document.createElement("strong");
      label.textContent = safeText(item[0]);
      var value = document.createElement("span");
      value.textContent = safeText(item[1]);
      badge.appendChild(label);
      badge.appendChild(value);
      container.appendChild(badge);
    });
  }

  function loadAuthRuntimePanel() {
    var statusPromise = state.apiAllowed
      ? fetchAuthRuntimeStatus().catch(function () {
        return fetchJson(AUTH_RUNTIME_DEMOS.status);
      })
      : fetchJson(AUTH_RUNTIME_DEMOS.status);
    Promise.all([
      statusPromise,
      fetchJson(AUTH_RUNTIME_DEMOS.preview)
    ])
      .then(function (payloads) {
        renderAuthRuntimeStatus(redact(payloads[0]));
        renderMockClaimsPreview(redact(payloads[1]));
      })
      .catch(function () {
        renderAuthRuntimeStatus({
          production_auth_enabled: false,
          auth_runtime_enabled: false,
          external_identity_provider_enabled: false,
          credentials_enabled: false,
          token_issuance_enabled: false,
          cookie_issuance_enabled: false,
          session_persistence_enabled: false,
          login_endpoint_enabled: false,
          logout_endpoint_enabled: false,
          blockers: [{ blocker_type: "generic", reason: "auth_runtime_demo_unavailable" }]
        });
        renderMockClaimsPreview({ status: "unavailable", roles: [] });
      });
  }

  function fetchAuthRuntimeStatus() {
    var endpoint = state.apiBase + "/brain/auth-runtime/status?scope=workspace:main";
    return fetch(endpoint).then(function (response) {
      if (!response.ok) {
        throw new Error("auth runtime status unavailable");
      }
      return response.json();
    });
  }

  function renderAuthRuntimeStatus(status) {
    var grid = document.getElementById("auth-runtime-status-grid");
    var blockers = document.getElementById("auth-runtime-blockers");
    if (!grid || !blockers) {
      return;
    }
    grid.textContent = "";
    [
      "production_auth_enabled",
      "auth_runtime_enabled",
      "external_identity_provider_enabled",
      "credentials_enabled",
      "token_issuance_enabled",
      "cookie_issuance_enabled",
      "session_persistence_enabled",
      "login_endpoint_enabled",
      "logout_endpoint_enabled"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(status && status[key]));
      grid.appendChild(card);
    });
    blockers.textContent = "";
    var items = status && Array.isArray(status.blockers) ? status.blockers : [];
    if (!items.length) {
      blockers.appendChild(emptyNote("Auth runtime blockers render here."));
      return;
    }
    items.forEach(function (item) {
      var badge = document.createElement("div");
      badge.className = "blocker-badge";
      var label = document.createElement("strong");
      label.textContent = safeText(item.blocker_type || item.reason || "disabled");
      var value = document.createElement("span");
      value.textContent = safeText(item.reason || "blocked by design");
      badge.appendChild(label);
      badge.appendChild(value);
      blockers.appendChild(badge);
    });
  }

  function renderMockClaimsPreview(preview) {
    var container = document.getElementById("mock-claims-preview");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["status", preview.status || "preview"],
      ["issuer", preview.issuer || "mock.local"],
      ["subject", preview.subject || "local.operator"],
      ["roles", Array.isArray(preview.roles) ? preview.roles.join(", ") : "operator"],
      ["production_identity", String(Boolean(preview.production_identity))],
      ["credentials_present", String(Boolean(preview.credentials_present))],
      ["token_present", String(Boolean(preview.token_present))],
      ["cookie_present", String(Boolean(preview.cookie_present))],
      ["session_persisted", String(Boolean(preview.session_persisted))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1] || "none");
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function loadConnectorRuntimePanels() {
    var statusPromise = state.apiAllowed
      ? fetchConnectorRuntimeStatus().catch(function () {
        return fetchJson(CONNECTOR_RUNTIME_DEMOS.status);
      })
      : fetchJson(CONNECTOR_RUNTIME_DEMOS.status);
    Promise.all([
      statusPromise,
      fetchJson(CONNECTOR_RUNTIME_DEMOS.preview)
    ])
      .then(function (payloads) {
        renderConnectorRuntimeStatus(redact(payloads[0]));
        renderConnectorBoundaryPreview(redact(payloads[1]));
      })
      .catch(function () {
        renderConnectorRuntimeStatus({
          connector_runtime_enabled: false,
          connector_external_calls_enabled: false,
          connector_credentials_enabled: false,
          connector_token_storage_enabled: false,
          connector_activation_enabled: false,
          connector_route_registration_enabled: false,
          blockers: [{ blocker_type: "generic", reason: "connector_runtime_demo_unavailable" }]
        });
        renderConnectorBoundaryPreview({ status: "unavailable", checks: [] });
      });
  }

  function fetchConnectorRuntimeStatus() {
    var endpoint = state.apiBase + "/brain/connector-runtime/status?scope=workspace:main";
    return fetch(endpoint).then(function (response) {
      if (!response.ok) {
        throw new Error("connector runtime status unavailable");
      }
      return response.json();
    });
  }

  function renderConnectorRuntimeStatus(status) {
    var grid = document.getElementById("connector-runtime-status-grid");
    var blockers = document.getElementById("connector-runtime-blockers");
    if (!grid || !blockers) {
      return;
    }
    grid.textContent = "";
    [
      "connector_runtime_enabled",
      "connector_external_calls_enabled",
      "connector_credentials_enabled",
      "connector_token_storage_enabled",
      "connector_activation_enabled",
      "connector_route_registration_enabled"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(status && status[key]));
      grid.appendChild(card);
    });
    blockers.textContent = "";
    var items = status && Array.isArray(status.blockers) ? status.blockers : [];
    if (!items.length) {
      blockers.appendChild(emptyNote("Connector runtime blockers render here."));
      return;
    }
    items.forEach(function (item) {
      var badge = document.createElement("div");
      badge.className = "blocker-badge";
      var label = document.createElement("strong");
      label.textContent = safeText(item.blocker_type || item.reason || "disabled");
      var value = document.createElement("span");
      value.textContent = safeText(item.reason || "blocked by design");
      badge.appendChild(label);
      badge.appendChild(value);
      blockers.appendChild(badge);
    });
  }

  function renderConnectorBoundaryPreview(preview) {
    var container = document.getElementById("connector-boundary-preview");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["status", preview.status || "preview"],
      ["manifest_valid", String(Boolean(preview.manifest_valid))],
      ["egress_allowed", String(Boolean(preview.egress_allowed))],
      ["external_call_allowed", String(Boolean(preview.external_call_allowed))],
      ["credentials_present", String(Boolean(preview.credentials_present))],
      ["trusted_ingress", String(Boolean(preview.trusted_ingress))],
      ["provenance_required", String(Boolean(preview.provenance_required))],
      ["redaction_applied", String(Boolean(preview.redaction_applied))]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1] || "none");
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function loadLocalSessionPanels() {
    var statusPromise = state.apiAllowed
      ? fetchLocalSessionStatus().catch(function () {
        return fetchJson(LOCAL_SESSION_DEMOS.status);
      })
      : fetchJson(LOCAL_SESSION_DEMOS.status);
    Promise.all([
      statusPromise,
      fetchJson(LOCAL_SESSION_DEMOS.preview)
    ])
      .then(function (payloads) {
        renderLocalSessionStatus(redact(payloads[0]));
        renderLocalSessionPreview(redact(payloads[1]));
      })
      .catch(function () {
        renderLocalSessionStatus({
          dev_only: true,
          read_only: true,
          production_session: false,
          credential_backed: false,
          token_issued: false,
          cookie_issued: false,
          persistent: false,
          write_allowed: false,
          execute_allowed: false,
          activation_allowed: false,
          external_calls_allowed: false,
          no_go_warnings: ["local_session_demo_unavailable"]
        });
        renderLocalSessionPreview({ roles: [], owner_scope: [] });
      });
  }

  function fetchLocalSessionStatus() {
    var endpoint = state.apiBase + "/brain/local-session/status?scope=workspace:main";
    return fetch(endpoint).then(function (response) {
      if (!response.ok) {
        throw new Error("local session status unavailable");
      }
      return response.json();
    });
  }

  function renderLocalSessionStatus(status) {
    var grid = document.getElementById("local-session-status-grid");
    var boundary = document.getElementById("local-session-boundary");
    if (!grid || !boundary) {
      return;
    }
    grid.textContent = "";
    [
      "dev_only",
      "read_only",
      "production_session",
      "credential_backed",
      "token_issued",
      "cookie_issued",
      "persistent",
      "write_allowed",
      "execute_allowed",
      "activation_allowed",
      "external_calls_allowed"
    ].forEach(function (key) {
      var card = document.createElement("div");
      card.className = "safety-card";
      card.textContent = key + "=" + String(Boolean(status && status[key]));
      grid.appendChild(card);
    });
    boundary.textContent = "";
    var items = status && Array.isArray(status.no_go_warnings) ? status.no_go_warnings : [];
    if (!items.length) {
      boundary.appendChild(emptyNote("Local session boundary warnings render here."));
      return;
    }
    items.forEach(function (item) {
      var badge = document.createElement("div");
      badge.className = "blocker-badge";
      var label = document.createElement("strong");
      label.textContent = safeText(item);
      var value = document.createElement("span");
      value.textContent = "blocked by design";
      badge.appendChild(label);
      badge.appendChild(value);
      boundary.appendChild(badge);
    });
  }

  function renderLocalSessionPreview(preview) {
    var container = document.getElementById("local-session-preview");
    if (!container) {
      return;
    }
    container.textContent = "";
    [
      ["status", preview.status || "active_local_preview"],
      ["session_type", preview.session_type || "local_preview"],
      ["actor_id", preview.actor_id || "local.operator"],
      ["roles", Array.isArray(preview.roles) ? preview.roles.join(", ") : "operator"],
      [
        "owner_scope",
        Array.isArray(preview.owner_scope) ? preview.owner_scope.join(", ") : "workspace:main"
      ],
      ["expires_at", preview.expires_at || "synthetic expiry"]
    ].forEach(function (item) {
      var row = document.createElement("div");
      row.className = "checklist-row";
      var label = document.createElement("span");
      label.textContent = item[0];
      var value = document.createElement("strong");
      value.textContent = safeText(item[1] || "none");
      row.appendChild(label);
      row.appendChild(value);
      container.appendChild(row);
    });
  }

  function operatorActionBlockers(model) {
    var blockers = [];
    if (Array.isArray(model.blockers)) {
      blockers = blockers.concat(model.blockers);
    }
    if (model.operator_action_blockers && Array.isArray(model.operator_action_blockers.blockers)) {
      blockers = blockers.concat(model.operator_action_blockers.blockers);
    }
    return blockers;
  }

  function lifecycleBlockers(model) {
    var blockers = [];
    if (Array.isArray(model.blockers)) {
      blockers = blockers.concat(model.blockers);
    }
    if (model.module_activation_blockers && Array.isArray(model.module_activation_blockers.blockers)) {
      blockers = blockers.concat(model.module_activation_blockers.blockers);
    }
    return blockers;
  }

  function emptyNote(message) {
    var note = document.createElement("p");
    note.className = "empty-note";
    note.textContent = message;
    return note;
  }

  function renderForbiddenActions(actions) {
    var container = document.getElementById("forbidden-actions");
    container.textContent = "";
    var list = actions.length ? actions : forbiddenFallback();
    list.forEach(function (action) {
      var card = document.createElement("div");
      card.className = "descriptor-card";
      var key = document.createElement("strong");
      key.textContent = safeText(action.action_key || "forbidden_action");
      var reason = document.createElement("p");
      reason.textContent = safeText(action.reason || "Descriptor only. Action disabled.");
      var button = document.createElement("button");
      button.className = "disabled-action";
      button.type = "button";
      button.disabled = true;
      button.textContent = "Disabled";
      card.appendChild(key);
      card.appendChild(reason);
      card.appendChild(button);
      container.appendChild(card);
    });
  }

  function collectActions(model) {
    var sections = Array.isArray(model.sections) ? model.sections : [];
    return sections.reduce(function (items, section) {
      var actions = Array.isArray(section.forbidden_actions) ? section.forbidden_actions : [];
      return items.concat(actions);
    }, []);
  }

  function forbiddenFallback() {
    return [
      { action_key: "activate_module", reason: "Disabled in static prototype." },
      { action_key: "activate_capability", reason: "Disabled in static prototype." },
      { action_key: "load_code", reason: "Code loading is unavailable." },
      { action_key: "execute_tool", reason: "Tool execution is unavailable." },
      { action_key: "enable_external_model_calls", reason: "External calls are unavailable." },
      { action_key: "hard_delete", reason: "Hard delete is unavailable." }
    ];
  }

  function listBlock(title, items) {
    var wrapper = document.createElement("div");
    if (!items.length) {
      return wrapper;
    }
    var heading = document.createElement("strong");
    heading.textContent = title;
    var list = document.createElement("ul");
    list.className = "list";
    items.slice(0, 4).forEach(function (item) {
      var entry = document.createElement("li");
      entry.textContent = safeText(typeof item === "string" ? item : summarizeObject(item));
      list.appendChild(entry);
    });
    wrapper.appendChild(heading);
    wrapper.appendChild(list);
    return wrapper;
  }

  function summarizeObject(item) {
    if (!item || typeof item !== "object") {
      return String(item);
    }
    return Object.keys(item).slice(0, 3).map(function (key) {
      return key + ": " + item[key];
    }).join(", ");
  }

  function pill(value) {
    var node = document.createElement("span");
    node.className = "pill " + String(value).toLowerCase();
    node.textContent = safeText(String(value));
    return node;
  }

  function labelFor(view) {
    return String(view || "overview").replace(/_/g, " ").replace(/\b\w/g, function (char) {
      return char.toUpperCase();
    });
  }

  function safeText(value) {
    return String(redact(value));
  }

  function setStatus(message) {
    document.getElementById("connection-status").textContent = message;
  }
}());
