# Capability Runtime Closed Registry

- `capability_runtime.health.read`: risk=low, approval_required=false, execution_kind=read_only_reference, side_effect_class=none
- `capability_runtime.observability.read`: risk=low, approval_required=false, execution_kind=read_only_reference, side_effect_class=none
- `capability_runtime.audit.read`: risk=medium, approval_required=true, execution_kind=read_only_reference, side_effect_class=none
- `capability.text.normalize`: risk=low, approval_required=false, execution_kind=pure_function, side_effect_class=none
- `capability.hash.sha256`: risk=low, approval_required=false, execution_kind=pure_function, side_effect_class=none
- `capability.json.validate`: risk=low, approval_required=false, execution_kind=pure_function, side_effect_class=none
- `connector.reference.read.simulate`: risk=medium, approval_required=true, execution_kind=synthetic_reference_connector, side_effect_class=none
- `connector.reference.write.preview`: risk=medium, approval_required=true, execution_kind=synthetic_reference_connector_preview, side_effect_class=none

All registry entries require operator_invoked=true, explicit_plan=true, sandboxed=true, deterministic=true, and every external, production, tool, network, filesystem, process, credential, and token effect false.
