"use strict";

(function () {
  var activated = false;
  var mutationNonce = "";
  var requestSequence = 0;
  var routes = {
    bootstrap: "/aion/local/v1/bootstrap",
    status: "/aion/local/v1/status",
    health: "/aion/local/v1/health",
    observability: "/aion/local/v1/observability",
    audit: "/aion/local/v1/audit",
    model: "/aion/local/v1/model/simulate",
    capability: "/aion/local/v1/capability/execute",
    connector: "/aion/local/v1/connector/simulate",
    kill: "/aion/local/v1/kill",
    close: "/aion/local/v1/session/close"
  };
  var confirmations = {
    modelText: "SIMULATE_REFERENCE_TEXT_MODEL",
    modelStructured: "SIMULATE_REFERENCE_STRUCTURED_MODEL",
    capability: "EXECUTE_REFERENCE_CAPABILITY",
    connectorRead: "SIMULATE_REFERENCE_CONNECTOR_READ",
    connectorPreview: "PREVIEW_REFERENCE_CONNECTOR_WRITE",
    kill: "ACTIVATE_LOCAL_KILL_SWITCH",
    close: "CLOSE_LOCAL_OPERATOR_SESSION"
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function nextRequestId(prefix) {
    requestSequence += 1;
    return prefix + "-" + String(requestSequence).padStart(3, "0");
  }

  function writeEvent(message, payload) {
    var lines = [message];
    if (payload) {
      lines.push(JSON.stringify(payload, null, 2));
    }
    byId("live-event-view").textContent = lines.join("\n");
  }

  function writeReceipt(payload) {
    byId("live-receipt-view").textContent = JSON.stringify(payload, null, 2);
  }

  function setStatus(id, value) {
    byId(id).textContent = value;
  }

  function clearTransientOutput() {
    byId("live-receipt-view").textContent = "No live receipt yet.";
    byId("live-event-view").textContent = activated ? "Live output cleared." : "Live mode inactive.";
  }

  function replaceNonce(response) {
    var replacement = response.headers.get("X-AION-Mutation-Nonce");
    if (replacement) {
      mutationNonce = replacement;
    }
  }

  function request(path, options) {
    if (!activated) {
      return Promise.reject(new Error("live mode is not active"));
    }
    if (path.indexOf("/aion/local/v1/") !== 0) {
      return Promise.reject(new Error("local route rejected"));
    }
    var requestOptions = Object.assign({
      method: "GET",
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      referrerPolicy: "no-referrer"
    }, options || {});
    return fetch(path, requestOptions).then(function (response) {
      replaceNonce(response);
      return response.json().then(function (payload) {
        if (!response.ok || payload.ok === false) {
          throw new Error(payload.error_code || "local request rejected");
        }
        return payload;
      });
    });
  }

  function post(path, confirmation, payload) {
    var headers = {
      "Content-Type": "application/json",
      "X-AION-Operator-Confirmation": confirmation,
      "X-AION-Mutation-Nonce": mutationNonce
    };
    return request(path, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(Object.assign({}, payload, {
        operator_confirmation: confirmation
      }))
    });
  }

  function activate() {
    activated = true;
    request(routes.bootstrap).then(function (payload) {
      setStatus("live-session-status", "active local loopback session");
      setStatus("live-authorization-status", payload.bootstrap.authorization_id);
      setStatus("live-origin-status", payload.bootstrap.bound_origin);
      setStatus("live-kill-status", "clear");
      writeReceipt(payload.bootstrap);
      writeEvent("Live local session activated.", {
        console_session_id: payload.bootstrap.console_session_id,
        nonce_fingerprint: payload.bootstrap.current_nonce_fingerprint
      });
    }).catch(function (error) {
      activated = false;
      mutationNonce = "";
      setStatus("live-session-status", "offline static fallback");
      writeEvent("Live bootstrap failed; static offline mode remains active.", {
        error_code: error.message
      });
    });
  }

  function refreshProjection(name) {
    request(routes[name]).then(function (payload) {
      writeReceipt(payload[name]);
      writeEvent("Read projection refreshed.", { projection: name });
      if (name === "status" && payload.status) {
        setStatus("live-session-status", payload.status.console_session_state);
        setStatus("live-kill-status", payload.status.kill_switch_state);
      }
    }).catch(function (error) {
      writeEvent("Read projection rejected.", { error_code: error.message });
    });
  }

  function runModel(mode) {
    var prompt = byId("live-model-prompt").value;
    var structured = {
      type: "object",
      properties: {
        summary: { type: "string" },
        synthetic: { type: "boolean" },
        trust: { type: "string", const: "untrusted" }
      },
      required: ["summary", "synthetic", "trust"],
      additionalProperties: false
    };
    post(
      routes.model,
      mode === "structured_json" ? confirmations.modelStructured : confirmations.modelText,
      {
        request_id: nextRequestId("model"),
        mode: mode,
        transient_prompt: prompt,
        structured_output_schema: mode === "structured_json" ? structured : null,
        safe_metadata: { operator_console: "live_local_loopback" }
      }
    ).then(function (payload) {
      byId("live-model-prompt").value = "";
      writeReceipt(payload.projection);
      writeEvent("Model simulation completed. Output remains untrusted.", {
        output: payload.transient_output,
        fingerprint: payload.transient_output_fingerprint
      });
    }).catch(function (error) {
      writeEvent("Model simulation rejected.", { error_code: error.message });
    });
  }

  function capabilityPayload(capabilityId, text) {
    if (capabilityId === "capability.json.validate") {
      return {
        document: { status: "ok" },
        schema: {
          type: "object",
          properties: { status: { type: "string", const: "ok" } },
          required: ["status"],
          additionalProperties: false
        }
      };
    }
    return { text: text };
  }

  function runCapability() {
    var capabilityId = byId("live-capability-select").value;
    var text = byId("live-capability-input").value;
    post(routes.capability, confirmations.capability, {
      request_id: nextRequestId("capability"),
      capability_id: capabilityId,
      transient_input: capabilityPayload(capabilityId, text),
      input_schema_id: capabilityId + ":input",
      output_schema_id: capabilityId + ":output",
      safe_metadata: { explicit_operator_selection: true }
    }).then(function (payload) {
      byId("live-capability-input").value = "";
      writeReceipt(payload.projection);
      writeEvent("Reference capability completed.", { output: payload.transient_output });
    }).catch(function (error) {
      writeEvent("Capability request rejected.", { error_code: error.message });
    });
  }

  function runConnector(operation) {
    var proposedValue = {};
    if (operation === "connector.reference.write.preview") {
      try {
        proposedValue = JSON.parse(byId("live-connector-value").value || "{}");
      } catch (error) {
        writeEvent("Connector preview JSON rejected.", { error_code: "invalid_preview_json" });
        return;
      }
    }
    post(
      routes.connector,
      operation === "connector.reference.write.preview"
        ? confirmations.connectorPreview
        : confirmations.connectorRead,
      {
        request_id: nextRequestId("connector"),
        operation: operation,
        fixture_id: "reference-fixture-AION-235",
        record_key: "record-001",
        transient_proposed_value: proposedValue,
        existing_approval_id: "approval-AION-237-synthetic-connector"
      }
    ).then(function (payload) {
      byId("live-connector-value").value = "";
      writeReceipt(payload.projection);
      writeEvent("Synthetic connector request completed.", {
        output: payload.transient_output,
        preview_only: operation === "connector.reference.write.preview"
      });
    }).catch(function (error) {
      writeEvent("Connector request rejected.", { error_code: error.message });
    });
  }

  function terminal(path, confirmation, label) {
    post(path, confirmation, {
      request_id: nextRequestId(label)
    }).then(function (payload) {
      mutationNonce = "";
      setStatus("live-session-status", payload.terminal);
      setStatus("live-kill-status", payload.terminal === "killed" ? "active" : "closed");
      writeReceipt(payload.receipt);
      writeEvent("Terminal local session action completed.", { terminal: payload.terminal });
    }).catch(function (error) {
      writeEvent("Terminal action rejected.", { error_code: error.message });
    });
  }

  function bindControls() {
    var controls = document.querySelectorAll("[data-live-control]");
    controls.forEach(function (control) {
      control.addEventListener("click", function () {
        var action = control.getAttribute("data-live-control");
        if (action === "activate") {
          activate();
        } else if (action === "model-text") {
          runModel("text");
        } else if (action === "model-json") {
          runModel("structured_json");
        } else if (action === "capability") {
          runCapability();
        } else if (action === "connector-read") {
          runConnector("connector.reference.read.simulate");
        } else if (action === "connector-preview") {
          runConnector("connector.reference.write.preview");
        } else if (action === "status" || action === "health" || action === "observability" || action === "audit") {
          refreshProjection(action);
        } else if (action === "kill") {
          terminal(routes.kill, confirmations.kill, "kill");
        } else if (action === "close") {
          terminal(routes.close, confirmations.close, "close");
        } else if (action === "clear") {
          clearTransientOutput();
        }
      });
    });
  }

  bindControls();
}());
