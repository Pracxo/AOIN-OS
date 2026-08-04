# AION-248 Retention Policy

Every live request uses `store=false`, `background=false`, and `stream=false`. No request contains tools, files, images, audio or `previous_response_id`.

The runner releases raw prompts, request bodies, response bodies, parsed provider payloads, authorization headers and credential references after projection. Committed evidence stores fingerprints, counts, latency and status only. It does not claim provider zero-data retention.
