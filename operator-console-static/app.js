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
    incidents: "demo-data/incidents-view-model.json",
    registry_integrity: "demo-data/settings-safety-view-model.json",
    settings_safety: "demo-data/settings-safety-view-model.json",
    audit_provenance: "demo-data/settings-safety-view-model.json"
  };
  var MODULE_LIFECYCLE_DEMOS = {
    generic_knowledge_trail: "demo-data/generic-knowledge-trail.json",
    module_activation_blockers: "demo-data/module-activation-blockers.json",
    module_mock_runtime_trail: "demo-data/module-mock-runtime-trail.json",
    module_review_checklist: "demo-data/module-review-checklist.json"
  };
  var apiConfig = resolveApiBase();
  var state = {
    apiBase: apiConfig.apiBase,
    activeView: "overview",
    apiAllowed: apiConfig.apiAllowed
  };

  document.addEventListener("DOMContentLoaded", function () {
    bindTabs();
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
        tabs.forEach(function (item) {
          item.classList.remove("is-active");
        });
        tab.classList.add("is-active");
        state.activeView = tab.getAttribute("data-view") || "overview";
        loadView(state.activeView);
      });
    });
  }

  function loadView(view) {
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

  function loadDemo(view) {
    if (view === "module_lifecycle") {
      loadModuleLifecycleDemo();
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
