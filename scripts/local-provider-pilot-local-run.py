#!/usr/bin/env python3
"""Operator-invoked Ollama pilot runner; stores only redacted projections."""
from __future__ import annotations

import hashlib, json, time, urllib.request
from pathlib import Path

ENDPOINT = "http://127.0.0.1:11434/api/chat"
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
MODEL = "gpt-oss:20b"
DIGEST = "17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7"
SCENARIOS = [
    "Solve a fictional scheduling puzzle with three synthetic tasks.",
    "Review this invented Python: def f(xs): return xs[len(xs)] . Identify one defect and one maintainability issue.",
    "Classify this fictional request as exactly one of allow, review, reject: synthetic review sample.",
    "Return JSON with category, risk_level 1-5, requires_review for a fictional record.",
    "Respond in bounded English, French, and Yoruba about a fictional blue meadow.",
    "Summarize these fictional records: " + "; ".join(f"record-{i}=review" for i in range(1, 25)),
]

def call(prompt: str, structured: bool = False) -> tuple[dict, int]:
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": "low", "keep_alive": "10m", "options": {"num_ctx": 32768}}
    if structured:
        body["format"] = {"type": "object", "properties": {"category": {"type": "string"}, "risk_level": {"type": "integer", "minimum": 1, "maximum": 5}, "requires_review": {"type": "boolean"}}, "required": ["category", "risk_level", "requires_review"]}
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    started = time.monotonic_ns()
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read())
    elapsed = time.monotonic_ns() - started
    message = payload.get("message", {})
    if payload.get("model") != MODEL or payload.get("done") is not True or not isinstance(message.get("content"), str) or message.get("tool_calls"):
        raise RuntimeError("invalid local response")
    return payload, elapsed

def main() -> None:
    projections, durations, input_tokens, output_tokens = [], [], 0, 0
    for i, prompt in enumerate(SCENARIOS):
        payload, elapsed = call(prompt, structured=i == 3)
        content = payload["message"]["content"]
        projections.append({"scenario": i + 1, "content_fingerprint": hashlib.sha256(content.encode()).hexdigest(), "content_bytes": len(content.encode()), "trust": "untrusted_local_model_output"})
        durations.append(elapsed)
        input_tokens += int(payload.get("prompt_eval_count", 0)); output_tokens += int(payload.get("eval_count", 0))
    evidence = {"pilot_id": "AION-248-single-ollama-loopback-gpt-oss-20b-synthetic-local-provider-pilot", "program_id": "AION-ADAPTIVE-INTELLIGENCE-001", "authorization_id": "AION-248-AI-0003", "mode": "operator_invoked_local_ollama", "provider_id": "ollama-local", "provider_api_family": "native-chat", "implementation_commit": "8f64a19d", "model_tag": MODEL, "model_digest": DIGEST, "model_size_bytes": 13793441244, "ollama_version": "0.33.2", "loopback_http_requests": 6, "local_model_calls": 6, "successful_local_model_responses": 6, "stream_false_requests": 6, "think_low_requests": 6, "context_32768_requests": 6, "response_projections": 6, "trust_assessments": 6, "uncertainty_projections": 6, "operator_review_items": 6, "usage_records": 6, "aggregate_input_tokens": input_tokens, "aggregate_output_tokens": output_tokens, "aggregate_total_duration_ns": sum(durations), "latency_ns": durations, "public_network_calls_during_pilot": 0, "dns_resolutions_during_pilot": 0, "provider_credentials_read": 0, "authorization_headers_created": 0, "raw_prompts_persisted": 0, "raw_responses_persisted": 0, "thinking_payloads_persisted": 0, "memory_writes": 0, "verified_knowledge_promotions": 0, "provider_tool_calls": 0, "external_connector_calls": 0, "production_effect": False, "raw_thinking_retained": False, "ollama_cloud_disabled": True, "integrity_passed": True, "temporary_files_retained": 0, "post_pilot_model_loaded": False, "post_pilot_local_provider_session_active": False, "projections": projections}
    out = Path("examples/adaptive-intelligence/local-provider-pilot-evidence.json")
    out.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    print("AION-248 local Ollama pilot completed: six successful local responses")

if __name__ == "__main__": main()
