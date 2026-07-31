# Model Gateway Fallback and Retry Implementation

Fallback and retry records are planning-only evidence. Fallback candidates are capped at three. Retry attempts are capped at two and include deterministic delay values only.

Automatic fallback execution and automatic retry execution remain false. No fallback or retry plan can call a provider, connector, tool, function, shell, subprocess, browser, module, or production runtime.
