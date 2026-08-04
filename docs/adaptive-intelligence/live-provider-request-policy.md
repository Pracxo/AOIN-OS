# AION-248 Request Policy

All six live requests are synthetic text-only scenarios. The payload allowlist is `model`, `input`, `store`, `background`, `stream`, `max_output_tokens`, and `reasoning.effort=low`.

The local policy rejects `tools`, `tool_choice`, `files`, `file_ids`, `previous_response_id`, image inputs, audio inputs, alternate models, `store=true`, `background=true` and `stream=true` before credential use or transport.
