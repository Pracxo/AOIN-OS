# Shadow-Mode Runtime Hold

Runtime hold requirements:

- `shadow_mode_authorized=true`
- `shadow_mode_implemented=false`
- `shadow_mode_runtime_enabled=false`
- `shadow_mode_source_rewrite_enabled=false`
- `shadow_mode_git_write_enabled=false`
- `shadow_mode_pr_creation_enabled=false`
- `shadow_mode_auto_merge_enabled=false`
- `shadow_mode_provider_call_enabled=false`
- `shadow_mode_connector_runtime_enabled=false`
- `shadow_mode_model_training_enabled=false`
- `continuous_background_shadow_loop_approved=false`
- `production_event_stream_subscription_approved=false`
- `production_shadow_mode_activation_approved=false`
- `network_call_approved=false`
- `external_connector_call_approved=false`
- `provider_sdk_approved=false`
- `source_file_mutation_approved=false`
- `canonical_repository_mutation_approved=false`
- `real_pull_request_creation_approved=false`
- `approval_creation_approved=false`
- `automatic_merge_approved=false`
- `production_canary_approved=false`
- `production_deployment_approved=false`
- `runtime_effect_approved=false`
- `v02_tag_created=false`
- `v02_release_created=false`

The runtime hold script must fail if any AION-178 source file exists during
AION-177, if any prohibited flag becomes true, or if v0.2 tags or releases
appear.
