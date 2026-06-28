package aion.brain

allowed_actions := {
	"event.ingest",
	"event.subscription.create",
	"event.subscription.read",
	"event.subscription.disable",
	"event.dispatch",
	"event.dispatch.read",
	"event.reaction.run",
	"event.reaction.noop",
	"event.dead_letter.read",
	"event.dead_letter.resolve",
	"event.dead_letter.replay",
	"command.dispatch",
	"command.read",
	"command.cancel",
	"idempotency.read",
	"outbox.enqueue",
	"outbox.read",
	"outbox.process",
	"outbox.cancel",
	"inbox.receive",
	"inbox.read",
	"inbox.process",
	"processing_lease.acquire",
	"processing_lease.release",
	"consistency.check",
	"consistency.repair",
	"api.request.read",
	"api.openapi_hygiene.read",
	"api.error_codes.read",
	"scenario.create",
	"scenario.read",
	"scenario.disable",
	"scenario.run",
	"scenario.seed_defaults",
	"demo_fixture.read",
	"demo_fixture.load",
	"release_baseline.run",
	"release_baseline.read",
	"version.manifest.create",
	"version.manifest.read",
	"version.manifest.freeze",
	"version.feature.create",
	"version.feature.read",
	"version.feature.deprecate",
	"compatibility.matrix.generate",
	"compatibility.matrix.read",
	"migration.baseline.generate",
	"release.artifact.generate",
	"freeze_gate.run",
	"freeze_gate.read",
	"release.package.create",
	"release.package.read",
	"release.package.validate",
	"release.handoff.read",
	"backup.create",
	"backup.read",
	"backup.validate",
	"backup.restore.preview",
	"backup.restore.apply",
	"performance.benchmark.create",
	"performance.benchmark.read",
	"performance.benchmark.run",
	"performance.baseline.create",
	"performance.baseline.read",
	"performance.budget.create",
	"performance.budget.read",
	"performance.summary.read",
	"performance.regression.read",
	"sdk.compatibility.check",
	"security.scan.run",
	"security.scan.read",
	"security.threat_model.create",
	"security.threat_model.read",
	"security.threat_model.update",
	"security.control.create",
	"security.control.read",
	"security.control.update",
	"security.hardening.run",
	"security.hardening.read",
	"runtime_config.profile.create",
	"runtime_config.profile.read",
	"runtime_config.profile.update",
	"runtime_config.feature_override.create",
	"runtime_config.feature_override.read",
	"runtime_config.feature_override.update",
	"runtime_config.snapshot.create",
	"runtime_config.snapshot.read",
	"runtime_config.validate",
	"runtime_config.status.read",
	"runtime_config.change.read",
	"resilience.status.read",
	"resilience.dependency.check",
	"resilience.dependency.read",
	"resilience.retry_policy.create",
	"resilience.retry_policy.read",
	"resilience.retry_policy.update",
	"resilience.circuit_breaker.create",
	"resilience.circuit_breaker.read",
	"resilience.circuit_breaker.update",
	"resilience.degraded.read",
	"resilience.degraded.resolve",
	"resilience.fault_rule.create",
	"resilience.fault_rule.read",
	"resilience.fault_rule.update",
	"resilience.test.run",
	"resilience.test.read",
	"audit.entry.write",
	"audit.entry.read",
	"audit.verify",
	"audit.checkpoint.create",
	"audit.checkpoint.read",
	"audit.provenance.write",
	"audit.provenance.read",
	"audit.provenance.delete",
	"audit.export",
	"audit.status.read",
	"operator.overview.read",
	"operator.cards.read",
	"operator.queues.read",
	"operator.actions.read",
	"operator.acknowledgement.create",
	"operator.acknowledgement.read",
	"operator.snapshot.create",
	"operator.snapshot.read",
	"operator.readiness.read",
	"operator.runbooks.read",
	"operator_console.view.read",
	"operator_console.workflow.read",
	"operator_console.audit.run",
	"operator_console.action.describe",
	"operator_console.query",
	"local_auth.roles.read",
	"local_auth.identity.simulate",
	"local_auth.console.filter",
	"local_auth.role_matrix.read",
	"local_auth.role_matrix.audit",
	"local_auth.audit.run",
	"local_auth.status.read",
	"local_session.preview.create",
	"local_session.context.read",
	"local_session.status.read",
	"local_session.boundary.check",
	"local_session.audit.run",
	"operator_action.request.create",
	"operator_action.request.read",
	"operator_action.request.update",
	"operator_action.preview.create",
	"operator_action.preview.read",
	"operator_action.blocker.read",
	"operator_action.blocker.update",
	"operator_action.review",
	"operator_action.query",
	"action_authorization.dry_run.authorize",
	"action_authorization.audit.run",
	"action_authorization.decision.read",
	"dialogue.session.create",
	"dialogue.session.read",
	"dialogue.session.update",
	"dialogue.message.create",
	"dialogue.message.read",
	"dialogue.message.delete",
	"dialogue.turn",
	"dialogue.clarification.create",
	"dialogue.clarification.read",
	"dialogue.clarification.update",
	"dialogue.response.compose",
	"dialogue.response.verify",
	"dialogue.response.deliver",
	"dialogue.feedback.create",
	"dialogue.feedback.read",
	"dialogue.memory_handoff",
	"belief.claim.create",
	"belief.claim.read",
	"belief.claim.update",
	"belief.claim.delete",
	"belief.support.create",
	"belief.support.read",
	"belief.support.delete",
	"belief.contradiction.create",
	"belief.contradiction.read",
	"belief.contradiction.resolve",
	"belief.truth_maintenance.run",
	"belief.query",
	"belief.claim.extract",
	"concept.create",
	"concept.read",
	"concept.update",
	"entity.create",
	"entity.read",
	"entity.update",
	"entity.delete",
	"entity.alias.create",
	"entity.alias.read",
	"entity.alias.delete",
	"entity.mention.create",
	"entity.mention.read",
	"entity.resolve",
	"entity.reference.create",
	"entity.reference.read",
	"entity.reference.delete",
	"entity.merge.propose",
	"entity.merge.read",
	"entity.merge.approve",
	"entity.split.propose",
	"entity.split.read",
	"entity.split.approve",
	"entity.extract_mentions",
	"situation.create",
	"situation.read",
	"situation.update",
	"situation.project",
	"situation.atom.create",
	"situation.atom.read",
	"situation.atom.update",
	"situation.atom.delete",
	"situation.transition.read",
	"situation.temporal_window.create",
	"situation.temporal_window.read",
	"situation.continuity.record",
	"situation.continuity.read",
	"decision.frame.create",
	"decision.frame.read",
	"decision.frame.update",
	"decision.option.create",
	"decision.option.read",
	"decision.option.update",
	"decision.utility_profile.create",
	"decision.utility_profile.read",
	"decision.utility_profile.update",
	"decision.evaluate",
	"decision.counterfactual.run",
	"decision.record.create",
	"decision.record.read",
	"decision.record.update",
	"decision.recommend",
	"outcome.create",
	"outcome.read",
	"outcome.update",
	"outcome.delete",
	"outcome.expected_effect.create",
	"outcome.expected_effect.read",
	"outcome.expected_effect.delete",
	"outcome.observed_effect.create",
	"outcome.observed_effect.read",
	"outcome.verify",
	"outcome.attribution.create",
	"outcome.attribution.read",
	"outcome.attribution.delete",
	"outcome.feedback.create",
	"outcome.feedback.read",
	"outcome.feedback.update",
	"outcome.learning_bridge",
	"learning.experience.create",
	"learning.experience.read",
	"learning.experience.update",
	"learning.experience.delete",
	"learning.query",
	"learning.pattern.mine",
	"learning.pattern.read",
	"learning.lesson.create",
	"learning.lesson.read",
	"learning.lesson.update",
	"learning.synthesize",
	"learning.synthesis.read",
	"learning.skill_suggestion.create",
	"learning.skill_suggestion.read",
	"learning.skill_suggestion.update",
	"learning.skill_suggestion.convert",
	"learning.regression_suggestion.create",
	"learning.regression_suggestion.read",
	"learning.regression_suggestion.update",
	"memory.retrieve",
	"memory.write",
	"memory.governance.rule.create",
	"memory.governance.rule.read",
	"memory.governance.rule.disable",
	"memory.governance.evaluate",
	"memory.decay.recompute",
	"memory.retention.sweep",
	"memory.forget.request",
	"memory.forget.execute",
	"memory.conflict.scan",
	"memory.conflict.read",
	"memory.conflict.resolve",
	"memory.compact",
	"context.compile",
	"intent.classify",
	"plan.create",
	"plan.execute",
	"execution.step",
	"approval.request",
	"risk.assess",
	"guardrail.rule.create",
	"guardrail.rule.read",
	"guardrail.rule.disable",
	"guardrail.evaluate",
	"approval.request.create",
	"approval.request.read",
	"approval.decision.create",
	"approval.request.cancel",
	"approval.expire",
	"reasoning.run",
	"model.provider.register",
	"model.provider.read",
	"model.provider.disable",
	"model.provider.health_check",
	"model.profile.register",
	"model.profile.read",
	"model.profile.disable",
	"model.gateway.complete",
	"model.route",
	"model.complete",
	"model.usage.read",
	"model.budget.create",
	"model.budget.read",
	"model.budget.update",
	"model_output.create",
	"model_output.read",
	"model_output.delete",
	"model_output.parse",
	"model_output.govern",
	"model_output.structured_validate",
	"model_output.response_candidate.create",
	"model_output.response_candidate.read",
	"model_output.response_candidate.update",
	"model_output.tool_intent.create",
	"model_output.tool_intent.read",
	"model_output.tool_intent.update",
	"action_proposal.create",
	"action_proposal.read",
	"action_proposal.update",
	"action_proposal.delete",
	"action_proposal.review",
	"action_proposal.handoff",
	"action_proposal.blocker.read",
	"action_proposal.blocker.update",
	"action_proposal.tool_intent.review",
	"action_proposal.handoff.read",
	"run_supervision.create",
	"run_supervision.read",
	"run_supervision.update",
	"run_supervision.delete",
	"run_supervision.sample",
	"run_supervision.control.request",
	"run_supervision.control.read",
	"run_supervision.control.handoff",
	"run_supervision.timeout_policy.create",
	"run_supervision.timeout_policy.read",
	"run_supervision.timeout_policy.update",
	"run_supervision.compensation.create",
	"run_supervision.compensation.read",
	"run_supervision.compensation.update",
	"run_supervision.compensation.convert",
	"run_supervision.report.create",
	"run_supervision.report.read",
	"notification.topic.create",
	"notification.topic.read",
	"notification.topic.update",
	"notification.subscription.create",
	"notification.subscription.read",
	"notification.subscription.update",
	"notification.publish",
	"notification.read",
	"notification.update",
	"alert.create",
	"alert.read",
	"alert.update",
	"escalation.policy.create",
	"escalation.policy.read",
	"escalation.policy.update",
	"escalation.evaluate",
	"escalation.read",
	"escalation.update",
	"notification.digest.create",
	"notification.digest.read",
	"incident.signal.create",
	"incident.signal.read",
	"incident.signal.update",
	"incident.rule.create",
	"incident.rule.read",
	"incident.rule.update",
	"incident.create",
	"incident.read",
	"incident.update",
	"incident.delete",
	"incident.correlate",
	"incident.root_cause.create",
	"incident.root_cause.read",
	"incident.root_cause.update",
	"incident.recovery_review.create",
	"incident.recovery_review.read",
	"registry.resource.create",
	"registry.resource.read",
	"registry.resource.update",
	"registry.link.create",
	"registry.link.read",
	"registry.link.update",
	"registry.link.delete",
	"registry.backlink.read",
	"registry.validate",
	"registry.rebuild",
	"registry.snapshot.create",
	"registry.snapshot.read",
	"registry.broken_reference.read",
	"registry.broken_reference.update",
	"registry.orphaned_resource.read",
	"registry.orphaned_resource.update",
	"contract_registry.resource.create",
	"contract_registry.resource.read",
	"contract_registry.resource.update",
	"contract_registry.interface.read",
	"contract_registry.snapshot.create",
	"contract_registry.snapshot.read",
	"contract_registry.rule.create",
	"contract_registry.rule.read",
	"contract_registry.rule.update",
	"contract_registry.compatibility.scan",
	"contract_registry.finding.read",
	"contract_registry.finding.update",
	"contract_registry.migration_note.create",
	"contract_registry.migration_note.read",
	"contract_registry.migration_note.update",
	"contract_registry.report.create",
	"contract_registry.report.read",
	"extension.package.create",
	"extension.package.read",
	"extension.package.update",
	"extension.package.delete",
	"extension.manifest.validate",
	"extension.dependency.read",
	"extension.capability_declaration.read",
	"extension.compatibility.check",
	"extension.intake",
	"extension.review",
	"extension.install_plan.create",
	"extension.install_plan.read",
	"extension.install_plan.update",
	"extension.query",
	"module_slot.create",
	"module_slot.read",
	"module_slot.update",
	"module_slot.delete",
	"capability_binding.create",
	"capability_binding.read",
	"capability_binding.update",
	"module_binding.validate",
	"module_binding.conflict.read",
	"module_binding.conflict.update",
	"module_mount_plan.create",
	"module_mount_plan.read",
	"module_mount_plan.update",
	"route_binding_preview.create",
	"route_binding_preview.read",
	"module_binding.query",
	"module_activation.request.create",
	"module_activation.request.read",
	"module_activation.request.update",
	"module_activation.request.delete",
	"module_activation.gate.run",
	"module_activation.gate.read",
	"module_activation.blocker.read",
	"module_activation.blocker.update",
	"module_activation.review.create",
	"module_activation.review.read",
	"module_activation.plan.create",
	"module_activation.plan.read",
	"module_activation.plan.update",
	"module_activation.query.read",
	"local_auth.roles.read",
	"local_auth.role_matrix.read",
	"local_auth.status.read",
	"local_session.status.read",
	"action_authorization.decision.read",
	"runtime.registration.preview.create",
	"runtime.registration.preview.read",
	"module_mock.profile.create",
	"module_mock.profile.read",
	"module_mock.profile.update",
	"module_mock.invoke",
	"module_mock.run.read",
	"module_mock.output.read",
	"module_mock.finding.read",
	"module_mock.finding.update",
	"module_mock.query",
	"model_provider.profile.create",
	"model_provider.profile.read",
	"model_provider.profile.update",
	"model_provider.egress.preview",
	"model_provider.simulate",
	"model_provider.readiness.assess",
	"model_provider.blocker.read",
	"model_provider.blocker.update",
	"model_provider.query",
	"conformance.profile.create",
	"conformance.profile.read",
	"conformance.profile.update",
	"conformance.test_vector.create",
	"conformance.test_vector.read",
	"conformance.test_vector.update",
	"conformance.run",
	"conformance.finding.read",
	"conformance.finding.update",
	"conformance.readiness.assess",
	"conformance.readiness.read",
	"conformance.query",
	"golden_path.scenario.create",
	"golden_path.scenario.read",
	"golden_path.fixture.create",
	"golden_path.fixture.read",
	"golden_path.run",
	"golden_path.run.read",
	"golden_path.assertion.evaluate",
	"golden_path.report.create",
	"golden_path.report.read",
	"golden_path.release_smoke.run",
	"golden_path.query",
	"bootstrap.profile.create",
	"bootstrap.profile.read",
	"bootstrap.profile.update",
	"bootstrap.seed_bundle.create",
	"bootstrap.seed_bundle.read",
	"bootstrap.seed_bundle.update",
	"bootstrap.seed.execute",
	"bootstrap.doctor.run",
	"bootstrap.finding.read",
	"bootstrap.finding.update",
	"bootstrap.run",
	"bootstrap.run.read",
	"bootstrap.report.create",
	"bootstrap.report.read",
	"bootstrap.query",
	"release_candidate.create",
	"release_candidate.read",
	"release_candidate.update",
	"release_candidate.matrix.create",
	"release_candidate.matrix.read",
	"release_candidate.matrix.update",
	"release_candidate.gate.run",
	"release_candidate.run.read",
	"release_candidate.finding.read",
	"release_candidate.finding.update",
	"release_candidate.evidence_pack.create",
	"release_candidate.evidence_pack.read",
	"release_candidate.report.create",
	"release_candidate.report.read",
	"release_candidate.query",
	"response.draft",
	"response.evaluate",
	"response.verify",
	"evaluation.score",
	"clarification.ask",
	"capability.list",
	"capability.register",
	"capability.invoke",
	"capability.bind_runtime",
	"module.runtime.register",
	"module.runtime.read",
	"module.runtime.health_check",
	"module.package.submit",
	"module.package.read",
	"module.package.disable",
	"module.package.certify",
	"module.contract_test.run",
	"module.scaffold.create",
	"module.compatibility.check",
	"sandbox.profile.create",
	"sandbox.profile.read",
	"sandbox.profile.disable",
	"sandbox.profile.validate",
	"sandbox.run",
	"runtime_permission.grant",
	"runtime_permission.read",
	"runtime_permission.revoke",
	"secret_ref.create",
	"secret_ref.read",
	"secret_ref.disable",
	"secret_ref.rotate",
	"connector.create",
	"connector.read",
	"connector.disable",
	"connector.validate",
	"goal.create",
	"goal.read",
	"goal.transition",
	"task.create",
	"task.read",
	"task.transition",
	"task.run",
	"schedule.create",
	"schedule.read",
	"schedule.update",
	"scheduler.schedule.create",
	"scheduler.schedule.read",
	"scheduler.schedule.update",
	"scheduler.schedule.delete",
	"scheduler.due_item.read",
	"scheduler.due_item.update",
	"scheduler.reminder.create",
	"scheduler.reminder.read",
	"scheduler.reminder.update",
	"scheduler.tick",
	"scheduler.policy.create",
	"scheduler.policy.read",
	"scheduler.policy.update",
	"scheduler.report.create",
	"scheduler.report.read",
	"workflow.create",
	"workflow.read",
	"workflow.activate",
	"workflow.disable",
	"workflow.run",
	"workflow.pause",
	"workflow.resume",
	"workflow.cancel",
	"workflow.retry",
	"workflow.scheduler.tick",
	"workflow.worker.start_once",
	"workflow.engine.status",
	"workflow.temporal.status",
	"workflow.heartbeat.write",
	"reflection.create",
	"reflection.read",
	"skill.candidate.create",
	"skill.candidate.read",
	"skill.candidate.update",
	"skill.promote",
	"skill.read",
	"skill.activate",
	"skill.disable",
	"skill.archive",
	"skill.match",
	"identity.actor.create",
	"identity.actor.read",
	"identity.actor.disable",
	"identity.workspace.create",
	"identity.workspace.read",
	"identity.workspace.archive",
	"identity.membership.create",
	"identity.membership.read",
	"identity.membership.revoke",
	"identity.permission.create",
	"identity.permission.read",
	"identity.permission.revoke",
	"scope.resolve",
	"evidence.create",
	"evidence.read",
	"evidence.search",
	"evidence.link",
	"evidence.ground",
	"evidence.delete",
	"grounding.source.create",
	"grounding.source.read",
	"grounding.citation.create",
	"grounding.citation.read",
	"grounding.citation.delete",
	"grounding.map",
	"grounding.verify",
	"grounding.coverage.read",
	"grounding.query",
	"grounding.unsupported.read",
	"visual.map.read",
	"visual.telemetry.read",
	"visual.stream.read",
	"visual.snapshot.create",
	"visual.snapshot.read",
	"visual.timeline.read",
	"observability.read",
	"observability.event.create",
	"lifecycle.policy.create",
	"lifecycle.policy.read",
	"lifecycle.policy.update",
	"lifecycle.classify",
	"lifecycle.classification.read",
	"lifecycle.evaluate",
	"lifecycle.archive_candidate.create",
	"lifecycle.archive_candidate.read",
	"lifecycle.archive_candidate.update",
	"lifecycle.redaction_candidate.create",
	"lifecycle.redaction_candidate.read",
	"lifecycle.redaction_candidate.update",
	"lifecycle.purge_preview.create",
	"lifecycle.purge_preview.read",
	"lifecycle.review.create",
	"lifecycle.review.read",
	"lifecycle.report.create",
	"lifecycle.report.read",
	"prompt.template.create",
	"prompt.template.read",
	"prompt.template.update",
	"prompt.fragment.create",
	"prompt.fragment.read",
	"prompt.fragment.update",
	"prompt.compile",
	"prompt.packet.read",
	"prompt.packet.delete",
	"prompt.boundary.check",
	"prompt.injection.read",
	"prompt.preview",
	"prompt.manifest.create",
	"prompt.manifest.read",
	"instruction.create",
	"instruction.read",
	"instruction.update",
	"instruction.resolve",
	"instruction.conflict.read",
	"instruction.conflict.update",
	"instruction.constraint.create",
	"instruction.constraint.read",
	"instruction.constraint.update",
	"instruction.style_profile.create",
	"instruction.style_profile.read",
	"instruction.style_profile.update",
	"preference.create",
	"preference.read",
	"preference.update",
	"preference.candidate.create",
	"preference.candidate.read",
	"preference.candidate.update",
	"explanation.create",
	"explanation.read",
	"explanation.verify",
	"explanation.feedback.create",
	"explanation.feedback.read",
	"explanation.why_not",
	"explanation.trace_narrative.create",
	"explanation.trace_narrative.read",
	"self_model.read",
	"self_model.update",
	"self_model.describe",
	"self_model.capability_awareness.read",
	"self_model.capability_awareness.refresh",
	"self_model.limitation.create",
	"self_model.limitation.read",
	"self_model.limitation.update",
	"self_model.confidence.calibrate",
	"self_model.confidence.read",
	"self_model.assessment.run",
	"self_model.assessment.read",
	"self_model.introspection.create",
	"self_model.introspection.read",
	"attention.focus.create",
	"attention.focus.read",
	"attention.focus.update",
	"attention.signal.create",
	"attention.signal.read",
	"attention.decide",
	"attention.signal.update",
	"working_memory.write",
	"working_memory.read",
	"working_memory.delete",
	"interrupt.create",
	"interrupt.read",
	"interrupt.decide",
	"context.budget.allocate",
	"autonomy.profile.create",
	"autonomy.profile.read",
	"autonomy.profile.disable",
	"autonomy.run_level.set",
	"autonomy.run_level.read",
	"autonomy.run_level.end",
	"autonomy.delegation.create",
	"autonomy.delegation.read",
	"autonomy.delegation.revoke",
	"autonomy.decide",
	"autonomy.status.read",
	"cycle.template.create",
	"cycle.template.read",
	"cycle.template.disable",
	"cycle.run",
	"cycle.read",
	"cycle.step.run",
	"cycle.status.read",
	"sleep_consolidation.run",
	"maintenance.run",
	"mcp.server.register",
	"mcp.server.read",
	"mcp.server.disable",
	"mcp.server.health_check",
	"mcp.tools.sync",
	"mcp.tool.invoke",
	"mcp.mapping.read",
	"mcp.mapping.write",
	"snapshot.create",
	"snapshot.read",
	"replay.run",
	"replay.read",
	"regression.case.create",
	"regression.case.read",
	"regression.case.update",
	"regression.run",
	"regression.read",
	"eval.adapter.run",
	"kernel.status.read",
	"kernel.boot.read",
	"kernel.services.read",
	"kernel.self_test.run",
	"kernel.contracts.export",
	"kernel.boundary_check.run",
	"policy.catalog.create",
	"policy.catalog.read",
	"policy.catalog.update",
	"policy.permission.create",
	"policy.permission.read",
	"policy.permission.update",
	"policy.role_template.create",
	"policy.role_template.read",
	"policy.role_template.update",
	"policy.simulate",
	"policy.test_case.create",
	"policy.test_case.read",
	"policy.test.run",
	"policy.coverage.read",
	"policy.bundle.export",
	"policy.opa.status",
	"trace.read",
	"learning.record",
	"learning.experience.create",
	"learning.experience.read",
	"learning.experience.update",
	"learning.query",
	"learning.pattern.mine",
	"learning.pattern.read",
	"learning.lesson.create",
	"learning.lesson.read",
	"learning.lesson.update",
	"learning.synthesize",
	"learning.synthesis.read",
	"learning.skill_suggestion.create",
	"learning.skill_suggestion.read",
	"learning.skill_suggestion.update",
	"learning.regression_suggestion.create",
	"learning.regression_suggestion.read",
	"learning.regression_suggestion.update",
}

valid_risks := {"low", "medium", "high", "critical"}
valid_runtime_types := {"local_internal", "local_stub", "http", "mcp"}

low_allowed_actions := {
	"event.ingest",
	"event.subscription.create",
	"event.subscription.read",
	"event.dispatch",
	"event.dispatch.read",
	"event.reaction.run",
	"event.reaction.noop",
	"event.dead_letter.read",
	"event.dead_letter.resolve",
	"event.dead_letter.replay",
	"command.dispatch",
	"command.read",
	"idempotency.read",
	"outbox.enqueue",
	"outbox.read",
	"inbox.receive",
	"inbox.read",
	"inbox.process",
	"processing_lease.acquire",
	"processing_lease.release",
	"consistency.check",
	"api.error_codes.read",
	"scenario.read",
	"demo_fixture.read",
	"release_baseline.read",
	"version.manifest.read",
	"version.feature.read",
	"compatibility.matrix.read",
	"freeze_gate.read",
	"release.package.read",
	"release.package.validate",
	"release.handoff.read",
	"backup.read",
	"backup.validate",
	"backup.restore.preview",
	"performance.benchmark.read",
	"performance.benchmark.run",
	"performance.baseline.read",
	"performance.budget.read",
	"performance.summary.read",
	"performance.regression.read",
	"sdk.compatibility.check",
	"memory.governance.rule.read",
	"memory.governance.evaluate",
	"memory.decay.recompute",
	"memory.retention.sweep",
	"memory.conflict.scan",
	"memory.conflict.read",
	"memory.forget.request",
	"context.compile",
	"intent.classify",
	"plan.create",
	"approval.request",
	"risk.assess",
	"guardrail.rule.read",
	"guardrail.evaluate",
	"approval.request.read",
	"approval.expire",
	"reasoning.run",
	"model_output.read",
	"model_output.parse",
	"model_output.structured_validate",
	"model_output.response_candidate.read",
	"model_output.tool_intent.read",
	"action_proposal.read",
	"action_proposal.blocker.read",
	"action_proposal.handoff.read",
	"run_supervision.read",
	"run_supervision.sample",
	"run_supervision.control.read",
	"run_supervision.timeout_policy.read",
	"run_supervision.compensation.read",
	"run_supervision.report.read",
	"notification.topic.read",
	"notification.subscription.read",
	"notification.read",
	"alert.read",
	"escalation.policy.read",
	"escalation.read",
	"notification.digest.read",
	"incident.signal.read",
	"incident.rule.read",
	"incident.read",
	"incident.root_cause.read",
	"incident.recovery_review.read",
	"registry.resource.read",
	"registry.link.read",
	"registry.backlink.read",
	"registry.snapshot.read",
	"registry.broken_reference.read",
	"registry.orphaned_resource.read",
	"response.draft",
	"response.evaluate",
	"response.verify",
	"evaluation.score",
	"clarification.ask",
	"capability.list",
	"module.runtime.read",
	"module.runtime.health_check",
	"module.package.read",
	"module.compatibility.check",
	"sandbox.profile.read",
	"sandbox.profile.validate",
	"runtime_permission.read",
	"secret_ref.read",
	"connector.read",
	"connector.validate",
	"goal.create",
	"goal.read",
	"goal.transition",
	"task.create",
	"task.read",
	"task.transition",
	"schedule.create",
	"schedule.read",
	"schedule.update",
	"scheduler.schedule.read",
	"scheduler.due_item.read",
	"scheduler.reminder.read",
	"scheduler.policy.read",
	"scheduler.report.read",
	"workflow.read",
	"workflow.engine.status",
	"workflow.temporal.status",
	"reflection.create",
	"reflection.read",
	"skill.candidate.create",
	"skill.candidate.read",
	"skill.read",
	"skill.match",
	"concept.create",
	"concept.read",
	"entity.create",
	"entity.read",
	"entity.alias.create",
	"entity.alias.read",
	"entity.mention.create",
	"entity.mention.read",
	"entity.resolve",
	"entity.reference.create",
	"entity.reference.read",
	"entity.extract_mentions",
	"evidence.read",
	"evidence.search",
	"evidence.ground",
	"grounding.source.read",
	"grounding.citation.read",
	"grounding.map",
	"grounding.verify",
	"grounding.coverage.read",
	"grounding.query",
	"grounding.unsupported.read",
	"visual.map.read",
	"visual.telemetry.read",
	"visual.snapshot.read",
	"visual.timeline.read",
	"observability.read",
	"contract_registry.resource.read",
	"contract_registry.interface.read",
	"contract_registry.snapshot.read",
	"contract_registry.rule.read",
	"contract_registry.finding.read",
	"contract_registry.migration_note.read",
	"contract_registry.report.read",
	"extension.package.read",
	"extension.manifest.validate",
	"extension.dependency.read",
	"extension.capability_declaration.read",
	"extension.install_plan.read",
	"extension.query",
	"module_slot.read",
	"capability_binding.read",
	"module_binding.conflict.read",
	"module_mount_plan.read",
	"route_binding_preview.read",
	"module_binding.query",
	"conformance.profile.read",
	"conformance.test_vector.read",
	"conformance.finding.read",
	"conformance.readiness.read",
	"conformance.query",
	"golden_path.scenario.read",
	"golden_path.fixture.read",
	"golden_path.run.read",
	"golden_path.report.read",
	"golden_path.release_smoke.run",
	"golden_path.query",
	"bootstrap.profile.read",
	"bootstrap.seed_bundle.read",
	"bootstrap.finding.read",
	"bootstrap.run.read",
	"bootstrap.report.read",
	"bootstrap.query",
	"release_candidate.read",
	"release_candidate.matrix.read",
	"release_candidate.run.read",
	"release_candidate.finding.read",
	"release_candidate.evidence_pack.read",
	"release_candidate.report.read",
	"release_candidate.query",
	"lifecycle.policy.read",
	"lifecycle.classify",
	"lifecycle.classification.read",
	"lifecycle.archive_candidate.read",
	"lifecycle.redaction_candidate.read",
	"lifecycle.purge_preview.read",
	"lifecycle.review.read",
	"lifecycle.report.create",
	"lifecycle.report.read",
	"prompt.template.read",
	"prompt.fragment.read",
	"prompt.packet.read",
	"prompt.injection.read",
	"prompt.preview",
	"prompt.manifest.read",
	"instruction.read",
	"instruction.create",
	"instruction.update",
	"instruction.resolve",
	"instruction.conflict.read",
	"instruction.conflict.update",
	"instruction.constraint.read",
	"instruction.constraint.create",
	"instruction.constraint.update",
	"instruction.style_profile.read",
	"instruction.style_profile.create",
	"instruction.style_profile.update",
	"preference.create",
	"preference.read",
	"preference.update",
	"preference.candidate.create",
	"preference.candidate.read",
	"preference.candidate.update",
	"explanation.create",
	"explanation.read",
	"explanation.verify",
	"explanation.feedback.create",
	"explanation.feedback.read",
	"explanation.why_not",
	"explanation.trace_narrative.create",
	"explanation.trace_narrative.read",
	"self_model.read",
	"self_model.update",
	"self_model.describe",
	"self_model.capability_awareness.read",
	"self_model.capability_awareness.refresh",
	"self_model.limitation.create",
	"self_model.limitation.read",
	"self_model.limitation.update",
	"self_model.confidence.calibrate",
	"self_model.confidence.read",
	"self_model.assessment.run",
	"self_model.assessment.read",
	"self_model.introspection.create",
	"self_model.introspection.read",
	"audit.entry.read",
	"audit.checkpoint.read",
	"audit.provenance.read",
	"audit.status.read",
	"attention.focus.create",
	"attention.focus.read",
	"attention.focus.update",
	"attention.signal.create",
	"attention.signal.read",
	"attention.decide",
	"attention.signal.update",
	"working_memory.write",
	"working_memory.read",
	"working_memory.delete",
	"interrupt.create",
	"interrupt.read",
	"interrupt.decide",
	"context.budget.allocate",
	"autonomy.profile.read",
	"autonomy.run_level.read",
	"autonomy.delegation.read",
	"autonomy.decide",
	"autonomy.status.read",
	"cycle.template.create",
	"cycle.template.read",
	"cycle.template.disable",
	"cycle.read",
	"cycle.status.read",
	"cycle.run",
	"cycle.step.run",
	"sleep_consolidation.run",
	"maintenance.run",
	"mcp.server.read",
	"mcp.server.health_check",
	"mcp.mapping.read",
	"kernel.status.read",
	"kernel.boot.read",
	"kernel.services.read",
	"policy.catalog.read",
	"policy.permission.read",
	"policy.role_template.read",
	"policy.test_case.read",
	"policy.coverage.read",
	"policy.opa.status",
	"trace.read",
	"learning.record",
}

medium_approval_actions := {
	"memory.write",
	"memory.governance.rule.create",
	"memory.governance.rule.disable",
	"memory.forget.execute",
	"memory.conflict.resolve",
	"capability.register",
	"capability.bind_runtime",
	"module.package.submit",
	"module.package.disable",
	"module.package.certify",
	"module.contract_test.run",
	"module.scaffold.create",
	"sandbox.profile.create",
	"sandbox.profile.disable",
	"sandbox.run",
	"runtime_permission.grant",
	"runtime_permission.revoke",
	"secret_ref.create",
	"secret_ref.disable",
	"secret_ref.rotate",
	"connector.create",
	"connector.disable",
	"mcp.server.register",
	"mcp.server.disable",
	"mcp.tools.sync",
	"mcp.mapping.write",
	"guardrail.rule.create",
	"guardrail.rule.disable",
	"approval.request.create",
	"approval.decision.create",
	"approval.request.cancel",
	"workflow.create",
	"workflow.activate",
	"workflow.disable",
	"workflow.pause",
	"workflow.resume",
	"workflow.cancel",
	"workflow.retry",
	"workflow.scheduler.tick",
	"workflow.worker.start_once",
	"workflow.heartbeat.write",
	"scheduler.schedule.create",
	"scheduler.schedule.update",
	"scheduler.schedule.delete",
	"scheduler.due_item.update",
	"scheduler.reminder.create",
	"scheduler.reminder.update",
	"scheduler.tick",
	"scheduler.policy.create",
	"scheduler.policy.update",
	"scheduler.report.create",
	"command.cancel",
	"outbox.process",
	"outbox.cancel",
	"consistency.repair",
	"backup.create",
	"performance.benchmark.create",
	"performance.baseline.create",
	"performance.budget.create",
	"model_output.create",
	"model_output.delete",
	"model_output.govern",
	"model_output.response_candidate.create",
	"model_output.response_candidate.update",
	"model_output.tool_intent.create",
	"model_output.tool_intent.update",
	"action_proposal.create",
	"action_proposal.update",
	"action_proposal.delete",
	"action_proposal.review",
	"action_proposal.handoff",
	"action_proposal.blocker.update",
	"action_proposal.tool_intent.review",
	"run_supervision.create",
	"run_supervision.update",
	"run_supervision.delete",
	"run_supervision.control.request",
	"run_supervision.control.handoff",
	"run_supervision.timeout_policy.create",
	"run_supervision.timeout_policy.update",
	"run_supervision.compensation.create",
	"run_supervision.compensation.update",
	"run_supervision.compensation.convert",
	"run_supervision.report.create",
	"notification.topic.create",
	"notification.topic.update",
	"notification.subscription.create",
	"notification.subscription.update",
	"notification.publish",
	"notification.update",
	"alert.create",
	"alert.update",
	"escalation.policy.create",
	"escalation.policy.update",
	"escalation.evaluate",
	"escalation.update",
	"notification.digest.create",
	"incident.signal.create",
	"incident.signal.update",
	"incident.rule.create",
	"incident.rule.update",
	"incident.create",
	"incident.update",
	"incident.delete",
	"incident.correlate",
	"incident.root_cause.create",
	"incident.root_cause.update",
	"incident.recovery_review.create",
	"registry.resource.create",
	"registry.resource.update",
	"registry.link.create",
	"registry.link.update",
	"registry.link.delete",
	"registry.validate",
	"registry.rebuild",
	"registry.snapshot.create",
	"registry.broken_reference.update",
	"registry.orphaned_resource.update",
}

default decision := {
	"allow": false,
	"approval_required": false,
	"reason": "policy_denied",
	"constraints": ["fail_closed"],
	"audit_level": "high",
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "snapshot_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "snapshot.read"
	input.context.actor_context.permissions[_] == "trace.read"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "snapshot_create_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "snapshot.create"
	snapshot_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "replay_allowed",
	"constraints": ["local_only", "side_effect_free"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "replay.run"
	replay_mode_allowed
	replay_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "replay_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "replay.read"
	input.context.actor_context.permissions[_] == "trace.read"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "regression_action_allowed",
	"constraints": ["local_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	regression_action
	regression_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_eval_adapter_allowed",
	"constraints": ["local_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "eval.adapter.run"
	input.context.adapter_name == "local"
	eval_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "model_registry_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	model_read_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "model_registry_admin_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	model_admin_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "deterministic_model_gateway_allowed",
	"constraints": ["local_or_deterministic"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	low_or_medium_risk
	input.action_type == "model.gateway.complete"
	not input.context.allow_external
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "model_budget_admin_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	model_budget_write_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "external_model_completion_allowed",
	"constraints": ["external_model_use"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	low_or_medium_risk
	input.action_type == "model.complete"
	external_model_allowed
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "visual_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	visual_read_action
	visual_read_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "grounding_read_allowed",
	"constraints": ["within_scope"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	grounding_read_action
	grounding_read_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "grounding_write_allowed",
	"constraints": ["soft_delete_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	grounding_write_action
	grounding_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "grounding_verify_allowed",
	"constraints": ["deterministic_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "grounding.verify"
	grounding_verifier
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "visual_stream_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "visual.stream.read"
	visual_stream_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "visual_snapshot_create_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "visual.snapshot.create"
	visual_snapshot_create_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "observability_event_create_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "observability.event.create"
	observability_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "contract_registry_read_allowed",
	"constraints": ["source_code_is_source_of_truth", "no_source_mutation"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	contract_registry_read_action
	contract_registry_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "contract_registry_advisory_action_allowed",
	"constraints": ["registry_indexes_only", "no_source_mutation", "no_code_generation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	contract_registry_advisory_action
	contract_registry_permission
	not contract_registry_source_mutation_requested
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "extension_registry_read_allowed",
	"constraints": ["metadata_only", "no_code_loading", "no_activation"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	extension_registry_read_action
	extension_registry_permission
	not extension_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "extension_registry_metadata_action_allowed",
	"constraints": ["metadata_only", "no_code_loading", "no_activation", "no_external_sources"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	extension_registry_metadata_action
	extension_registry_permission
	not extension_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_binding_read_allowed",
	"constraints": ["metadata_only", "no_module_activation", "no_capability_execution", "no_dynamic_route_registration"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	module_binding_read_action
	module_binding_permission
	not module_binding_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_binding_metadata_action_allowed",
	"constraints": ["metadata_only", "no_module_activation", "no_capability_execution", "no_dynamic_route_registration", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	module_binding_metadata_action
	module_binding_permission
	not module_binding_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_activation_read_allowed",
	"constraints": ["metadata_only", "activation_disabled", "no_capability_execution", "no_runtime_registration"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	module_activation_read_action
	module_activation_permission
	not module_activation_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_activation_metadata_action_allowed",
	"constraints": ["metadata_only", "activation_disabled", "no_capability_execution", "no_runtime_registration", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	module_activation_metadata_action
	module_activation_permission
	not module_activation_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_mock_read_allowed",
	"constraints": ["metadata_only", "dry_run_only", "synthetic_output_only", "no_activation", "no_capability_execution", "no_external_calls"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	module_mock_read_action
	module_mock_permission
	not module_mock_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_mock_metadata_action_allowed",
	"constraints": ["metadata_only", "dry_run_only", "synthetic_output_only", "no_code_loading", "no_package_install", "no_activation", "no_capability_execution", "no_external_calls", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	module_mock_metadata_action
	module_mock_permission
	not module_mock_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "model_provider_hardening_read_allowed",
	"constraints": ["metadata_only", "provider_disabled", "no_external_model_calls", "no_credentials"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	model_provider_read_action
	model_provider_permission
	not model_provider_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "model_provider_hardening_action_allowed",
	"constraints": ["metadata_only", "dry_run_only", "provider_disabled", "no_prompt_transmission", "no_external_model_calls", "no_credentials", "no_tool_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	model_provider_metadata_action
	model_provider_permission
	not model_provider_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "conformance_read_allowed",
	"constraints": ["metadata_only", "no_code_loading", "no_package_install", "no_activation", "no_external_calls"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	conformance_read_action
	conformance_permission
	not conformance_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "conformance_metadata_action_allowed",
	"constraints": ["metadata_only", "no_code_loading", "no_package_install", "no_activation", "no_external_calls", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	conformance_metadata_action
	conformance_permission
	not conformance_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "golden_path_read_allowed",
	"constraints": ["local_only", "dry_run_default", "no_external_calls", "no_tool_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	golden_path_read_action
	golden_path_permission
	not golden_path_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "golden_path_metadata_action_allowed",
	"constraints": ["scenario_owned_records_only", "dry_run_default", "no_external_calls", "no_tool_execution", "no_shell_execution", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	golden_path_metadata_action
	golden_path_permission
	not golden_path_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "bootstrap_read_allowed",
	"constraints": ["local_only", "scope_required", "no_external_calls"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	bootstrap_read_action
	bootstrap_permission
	not bootstrap_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "bootstrap_metadata_action_allowed",
	"constraints": ["local_only", "dry_run_default", "idempotent_defaults_only", "no_external_calls", "no_package_install", "no_production_secrets", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	bootstrap_metadata_action
	bootstrap_permission
	bootstrap_mode_allowed
	not bootstrap_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "release_candidate_read_allowed",
	"constraints": ["local_only", "rc_owned_records_only", "no_external_calls"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	release_candidate_read_action
	release_candidate_permission
	not release_candidate_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "release_candidate_metadata_action_allowed",
	"constraints": ["local_only", "rc_owned_records_only", "no_external_calls", "no_deploy", "no_publish", "no_source_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	release_candidate_metadata_action
	release_candidate_permission
	release_candidate_mode_allowed
	not release_candidate_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "lifecycle_read_allowed",
	"constraints": ["advisory_only", "source_records_not_mutated"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	lifecycle_read_action
	lifecycle_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "lifecycle_advisory_action_allowed",
	"constraints": ["advisory_only", "source_records_not_mutated", "hard_delete_disabled"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	lifecycle_advisory_action
	lifecycle_permission
	not lifecycle_hard_delete_requested
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "prompt_read_allowed",
	"constraints": ["provider_neutral_contracts_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	prompt_read_action
	prompt_read_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "prompt_write_allowed",
	"constraints": ["no_rendered_prompt_persistence"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	prompt_write_action
	prompt_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "prompt_compile_allowed",
	"constraints": ["boundary_check_required", "model_input_manifest_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "prompt.compile"
	prompt_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "security_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	security_read_action
	security_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "security_run_allowed",
	"constraints": ["local_security_baseline_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	security_run_action
	security_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "security_admin_allowed",
	"constraints": ["generic_security_baseline_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	security_admin_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "runtime_config_read_allowed",
	"constraints": ["metadata_only", "no_raw_secrets"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	runtime_config_read_action
	runtime_config_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "runtime_config_write_allowed",
	"constraints": ["safe_metadata_only", "no_process_env_mutation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	runtime_config_write_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "resilience_read_allowed",
	"constraints": ["local_resilience_metadata_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	resilience_read_action
	resilience_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "resilience_write_allowed",
	"constraints": ["bounded_retry", "local_only", "no_cloud_failover"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	resilience_write_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "resilience_fault_injection_allowed",
	"constraints": ["development_only", "fault_injection_disabled_by_default"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	resilience_fault_rule_write_action
	admin_or_owner
	development_env
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "resilience_test_allowed",
	"constraints": ["dry_run_default", "no_background_workers"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "resilience.test.run"
	resilience_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "audit_read_allowed",
	"constraints": ["local_audit_metadata_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	audit_read_action
	audit_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "audit_write_allowed",
	"constraints": ["append_only", "redacted_payloads"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	audit_write_action
	audit_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "audit_provenance_delete_allowed",
	"constraints": ["soft_delete_only", "append_correction_event"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "audit.provenance.delete"
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "audit_export_allowed",
	"constraints": ["local_export_only", "redaction_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "audit.export"
	audit_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_read_allowed",
	"constraints": ["read_only", "no_remediation"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	operator_read_action
	operator_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_console_audit_allowed",
	"constraints": ["read_only", "redacted", "no_frontend_runtime"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "operator_console.audit.run"
	operator_console_auditor
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_auth_read_allowed",
	"constraints": ["dev_only", "read_only", "no_production_auth", "no_credentials", "no_sessions", "no_external_identity"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	local_auth_read_action
	local_auth_actor
	not local_auth_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_auth_simulation_allowed",
	"constraints": ["dev_only", "synthetic_identity_only", "no_production_auth", "no_credentials", "no_sessions", "no_execution_grant", "no_activation_grant"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "local_auth.identity.simulate"
	local_auth_dev_context
	local_auth_operator
	not local_auth_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_auth_console_filter_allowed",
	"constraints": ["dev_only", "read_only", "redaction_required", "no_write_actions", "no_execution_grant", "no_activation_grant"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "local_auth.console.filter"
	local_auth_actor
	not local_auth_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_auth_audit_allowed",
	"constraints": ["dev_only", "read_only", "no_production_auth", "no_credentials", "no_sessions", "no_external_identity"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "local_auth.audit.run"
	local_auth_actor
	not local_auth_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_auth_role_matrix_audit_allowed",
	"constraints": ["dev_only", "read_only", "redaction_required", "no_write_actions", "no_execution_grant", "no_activation_grant"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "local_auth.role_matrix.audit"
	local_auth_actor
	not local_auth_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_session_read_allowed",
	"constraints": ["dev_only", "read_only", "no_production_auth", "no_credentials", "no_tokens", "no_cookies", "no_persistence", "no_external_identity"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	local_session_read_action
	local_auth_actor
	not local_session_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_session_preview_allowed",
	"constraints": ["dev_only", "synthetic_session_preview_only", "read_only", "no_login", "no_logout", "no_credentials", "no_tokens", "no_cookies", "no_persistence"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "local_session.preview.create"
	local_auth_dev_context
	local_auth_operator
	not local_session_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_session_boundary_allowed",
	"constraints": ["dev_only", "read_only", "no_credentials", "no_tokens", "no_cookies", "no_persistence", "no_execution_grant", "no_activation_grant", "no_external_calls"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	local_session_boundary_action
	local_auth_actor
	not local_session_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_acknowledgement_allowed",
	"constraints": ["acknowledgement_only", "does_not_resolve_source"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "operator.acknowledgement.create"
	operator_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_snapshot_create_allowed",
	"constraints": ["local_metadata_only", "no_remediation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "operator.snapshot.create"
	operator_snapshot_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "action_authorization_dry_run_allowed",
	"constraints": ["dry_run_only", "preview_or_review_only", "no_write", "no_execution", "no_activation", "no_external_calls"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "action_authorization.dry_run.authorize"
	input.context.dry_run_only == true
	not action_authorization_unsafe_request
	operator_writer
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "action_authorization_audit_allowed",
	"constraints": ["dry_run_only", "read_only", "no_write", "no_execution", "no_activation", "no_external_calls"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "action_authorization.audit.run"
	not action_authorization_unsafe_request
	action_authorization_auditor
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "action_authorization_decision_read_allowed",
	"constraints": ["dry_run_only", "read_only", "no_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "action_authorization.decision.read"
	not action_authorization_unsafe_request
	operator_reader
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "action_authorization_privileged_boundary_denied",
	"constraints": ["dry_run_only", "write_denied", "execution_denied", "activation_denied", "external_calls_denied"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	action_authorization_action
	action_authorization_unsafe_request
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_action_read_allowed",
	"constraints": ["dry_run_only", "read_only", "no_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	operator_action_read
	operator_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "operator_action_write_allowed",
	"constraints": ["dry_run_only", "record_only", "no_execution", "no_external_calls", "no_activation"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	operator_action_write
	operator_writer
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "dialogue_controlled_mode_denied",
	"constraints": ["controlled_execution_not_allowed_from_dialogue"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "dialogue.turn"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dialogue_action_allowed",
	"constraints": ["backend_only", "no_external_delivery"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	dialogue_action
	not dialogue_controlled_mode
	input.action_type != "dialogue.memory_handoff"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dialogue_memory_handoff_allowed",
	"constraints": ["memory_governance_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "dialogue.memory_handoff"
	input.risk_level == "medium"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_read_allowed",
	"constraints": ["belief_status_and_confidence_required"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	belief_read_action
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_claim_create_allowed",
	"constraints": ["no_memory_auto_promotion", "explicit_belief_status_required"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "belief.claim.create"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_claim_extract_allowed",
	"constraints": ["deterministic_extraction_only", "explicit_request_required"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "belief.claim.extract"
	permissions_within_scope
	input.context.explicit_request == true
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_mutation_allowed",
	"constraints": ["soft_delete_only", "revision_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	belief_mutation_action
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_internal_support_allowed",
	"constraints": ["support_contract_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "belief.support.create"
	belief_internal_or_admin
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_truth_maintenance_dry_run_allowed",
	"constraints": ["dry_run_default"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "belief.truth_maintenance.run"
	input.context.dry_run == true
	belief_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "belief_truth_maintenance_write_allowed",
	"constraints": ["revision_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "belief.truth_maintenance.run"
	input.context.dry_run == false
	admin_or_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "registry_action_allowed",
	"constraints": ["canonical_reference_contracts_required"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	registry_action
	not registry_approval_action
	input.risk_level != "critical"
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "registry_action_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	registry_approval_action
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "registry_action_approved",
	"constraints": ["approval_record_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	registry_approval_action
	input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "policy_catalog_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	policy_catalog_read_action
	policy_catalog_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "policy_catalog_admin_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	policy_catalog_admin_action
	policy_catalog_admin
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "policy_catalog_audit_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	policy_catalog_audit_action
	policy_catalog_auditor
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "mcp_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	mcp_read_action
	mcp_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "mcp_admin_action_allowed",
	"constraints": ["mcp_governed_by_aion"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	mcp_admin_action
	mcp_operator
	input.approval_present
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "mcp_admin_action_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	mcp_admin_action
	mcp_operator
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "mcp_dry_run_invocation_allowed",
	"constraints": ["no_external_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "mcp.tool.invoke"
	low_or_medium_risk
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_package_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "module.package.read"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_scaffold_allowed",
	"constraints": ["contracts_only", "no_code_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "module.scaffold.create"
	module_developer_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_compatibility_check_allowed",
	"constraints": ["contracts_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "module.compatibility.check"
	low_or_medium_risk
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_package_submit_allowed",
	"constraints": ["certification_required_before_runtime"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "module.package.submit"
	module_developer_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_package_certify_allowed",
	"constraints": ["dry_run_only", "no_code_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "module.package.certify"
	module_developer_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_package_disable_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "module.package.disable"
	module_developer_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_contract_test_allowed",
	"constraints": ["dry_run_only", "no_code_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "module.contract_test.run"
	module_developer_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "sandbox_read_allowed",
	"constraints": ["metadata_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "sandbox.profile.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "sandbox_validate_allowed",
	"constraints": ["no_code_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "sandbox.profile.validate"
	low_or_medium_risk
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "sandbox_dry_run_allowed",
	"constraints": ["no_code_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "sandbox.run"
	input.context.mode == "dry_run"
	low_or_medium_risk
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "sandbox_controlled_execution_disabled",
	"constraints": ["sandbox_execution_disabled"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "sandbox.run"
	input.context.mode == "controlled"
	not input.context.sandbox_execution_enabled
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "runtime_permission_read_allowed",
	"constraints": ["metadata_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "runtime_permission.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "secret_ref_read_allowed",
	"constraints": ["no_raw_secret_material"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "secret_ref.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "connector_read_allowed",
	"constraints": ["metadata_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "connector.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "connector_validate_allowed",
	"constraints": ["no_external_connection"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "connector.validate"
	low_or_medium_risk
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "mcp_controlled_invocation_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "mcp.tool.invoke"
	input.context.mode == "controlled"
	controlled_mcp_risk_requires_approval
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "mcp_controlled_invocation_allowed",
	"constraints": ["mcp_enabled", "capability_permission_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "mcp.tool.invoke"
	input.context.mode == "controlled"
	input.context.mcp_enabled == true
	mcp_invoke_permission
	mcp_transport_allowed
	mcp_risk_approved
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "mcp_not_enabled",
	"constraints": ["mcp_enabled_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "mcp.tool.invoke"
	input.context.mode == "controlled"
	not input.context.mcp_enabled
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "kernel_dev_action_allowed",
	"constraints": ["development_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	kernel_dev_action
	dev_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "kernel_contract_export_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "kernel.contracts.export"
	kernel_contract_exporter
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "api_error_codes_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "api.error_codes.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "api_request_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "api.request.read"
	api_support_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "api_openapi_hygiene_read_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "api.openapi_hygiene.read"
	api_support_admin
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scenario_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "scenario.read"
	input.risk_level == "low"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scenario_dry_run_allowed",
	"constraints": ["dry_run", "no_external_side_effects"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "scenario.run"
	input.context.mode == "dry_run"
	low_or_medium_risk
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "controlled_scenarios_disabled",
	"constraints": ["scenario_controlled_mode_disabled"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "scenario.run"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scenario_admin_allowed",
	"constraints": ["generic_scenarios_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	scenario_admin_action
	low_or_medium_risk
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "demo_fixture_dry_run_allowed",
	"constraints": ["generic_fixtures_only", "no_external_side_effects"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "demo_fixture.load"
	input.context.dry_run == true
	low_or_medium_risk
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "release_baseline_allowed",
	"constraints": ["dry_run", "generic_scenarios_only"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "release_baseline.run"
	low_or_medium_risk
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "unknown_action_type",
	"constraints": ["action_type_not_allowed"],
	"audit_level": "high",
} if {
	not valid_action
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "unknown_risk_level",
	"constraints": ["risk_level_not_allowed"],
	"audit_level": "high",
} if {
	valid_action
	not valid_risk
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "actor_context_required",
	"constraints": ["actor_context_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	identity_or_scope_action
	not actor_context_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dev_owner_identity_action_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	identity_action
	dev_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "identity_read_permission_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	identity_read_action
	permission_present
	not dev_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "identity_mutation_admin_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	identity_mutation_action
	admin_or_owner
	not dev_owner
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scope_resolution_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	scope_action
	actor_context_present
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "restricted_evidence_permission_required",
	"constraints": ["evidence.restricted.read_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	evidence_read_action
	input.context.sensitivity == "restricted"
	not evidence_restricted_read
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "evidence_read_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	evidence_read_action
	permissions_within_scope
	not restricted_evidence_without_permission
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "evidence_create_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	low_or_medium_risk
	input.action_type == "evidence.create"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scheduler_read_allowed",
	"constraints": ["local_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	scheduler_read_action
	scheduler_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scheduler_write_allowed",
	"constraints": ["local_only", "no_target_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	scheduler_write_action
	scheduler_writer
	not scheduler_external_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scheduler_tick_dry_run_allowed",
	"constraints": ["dry_run", "local_only", "no_target_execution"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "scheduler.tick"
	input.context.mode == "dry_run"
	scheduler_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "scheduler_tick_controlled_allowed",
	"constraints": ["controlled_local_records_only", "no_target_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "scheduler.tick"
	input.context.mode == "controlled"
	scheduler_operator
	not scheduler_external_action
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "scheduled_target_execution_denied",
	"constraints": ["scheduled_execution_disabled", "external_calendar_disabled"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	scheduler_action
	scheduler_external_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "incident_read_allowed",
	"constraints": ["local_only"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	incident_read_action
	incident_reader
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "incident_write_allowed",
	"constraints": ["local_only", "no_source_mutation", "no_remediation_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	incident_write_action
	incident_operator
	not incident_external_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "incident_correlate_dry_run_allowed",
	"constraints": ["dry_run", "local_only", "no_source_mutation"],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "incident.correlate"
	input.context.mode == "dry_run"
	incident_operator
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "incident_correlate_controlled_allowed",
	"constraints": ["incident_owned_records_only", "no_source_mutation", "no_remediation_execution"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "incident.correlate"
	input.context.mode == "controlled"
	incident_operator
	not incident_external_action
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "incident_remediation_denied",
	"constraints": ["source_mutation_denied", "remediation_execution_denied"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	incident_action
	incident_external_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "evidence_link_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "evidence.link"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "evidence_ground_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	low_or_medium_risk
	input.action_type == "evidence.ground"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "low_risk_memory_retrieval_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "memory.retrieve"
	permissions_within_scope
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "requested_permission_out_of_scope",
	"constraints": ["permission_scope_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "memory.retrieve"
	not permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "low_risk_memory_write_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "memory.write"
	permissions_within_scope
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "requested_permission_out_of_scope",
	"constraints": ["permission_scope_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "memory.write"
	not permissions_within_scope
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "unknown_execution_mode",
	"constraints": ["execution_mode_not_allowed"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	execution_action
	not valid_execution_mode
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "unknown_runtime_type",
	"constraints": ["runtime_type_not_allowed"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "module.runtime.register"
	not valid_runtime_type
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "runtime_type_not_executable_in_v0",
	"constraints": ["runtime_adapter_placeholder_only"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "capability.invoke"
	input.context.mode == "controlled"
	non_executable_runtime_type
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dry_run_execution_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "plan.execute"
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dry_run_step_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "execution.step"
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "controlled_execution_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "plan.execute"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "controlled_step_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "execution.step"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "dry_run_capability_invocation_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "capability.invoke"
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "controlled_capability_invocation_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "capability.invoke"
	input.context.mode == "controlled"
	not non_executable_runtime_type
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "unknown_task_run_mode",
	"constraints": ["task_run_mode_not_allowed"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	input.action_type == "task.run"
	not valid_task_run_mode
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "task_dry_run_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.action_type == "task.run"
	low_or_medium_risk
	input.context.run_mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "controlled_task_run_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "task.run"
	low_or_medium_risk
	input.context.run_mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_model_route_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "model.route"
	local_model_provider
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_model_completion_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	input.action_type == "model.complete"
	local_model_provider
}

decision := {
	"allow": false,
	"approval_required": false,
	"reason": "model_provider_not_allowed",
	"constraints": ["local_model_provider_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	low_or_medium_risk
	model_action
	not local_model_provider
	not external_model_allowed
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "memory_forget_request_allowed",
	"constraints": ["forgetting_requires_governance_workflow"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.action_type == "memory.forget.request"
	permissions_within_scope
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "low_risk_action_allowed",
	"constraints": [],
	"audit_level": "standard",
} if {
	valid_action
	valid_risk
	input.risk_level == "low"
	low_allowed_actions[input.action_type]
	input.action_type != "scenario.read"
	not identity_or_scope_action
	not evidence_action
	not visual_or_observability_action
	not security_action
	not runtime_config_action
	not resilience_action
	not audit_action
	not mcp_action
	not api_support_action
	not dialogue_action
	not prompt_action
	not belief_action
	not registry_action
	not contract_registry_action
	not extension_registry_action
	not module_binding_action
	not module_activation_action
	not module_mock_action
	not model_provider_hardening_action
	not conformance_action
	not golden_path_action
	not bootstrap_action
	not release_candidate_action
	not scheduler_action
	not incident_action
	not lifecycle_action
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_model_route_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "model.route"
	local_model_provider
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "local_model_completion_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "model.complete"
	local_model_provider
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "module_runtime_registration_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "module.runtime.register"
	valid_runtime_type
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "module_runtime_registration_approved",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "module.runtime.register"
	valid_runtime_type
	input.approval_present
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "medium_risk_action_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	medium_approval_actions[input.action_type]
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_risk_action_approved",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	medium_approval_actions[input.action_type]
	input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_dry_run_capability_invocation_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "capability.invoke"
	input.context.mode == "dry_run"
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "medium_controlled_capability_invocation_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "capability.invoke"
	input.context.mode == "controlled"
	not input.approval_present
	not non_executable_runtime_type
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_controlled_capability_invocation_approved",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "capability.invoke"
	input.context.mode == "controlled"
	input.approval_present
	not non_executable_runtime_type
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_risk_action_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "plan.execute"
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_dry_run_step_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "execution.step"
	input.context.mode == "dry_run"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_controlled_execution_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "plan.execute"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_controlled_step_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type == "execution.step"
	input.context.mode == "controlled"
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "medium_risk_action_allowed",
	"constraints": [],
	"audit_level": "elevated",
} if {
	valid_action
	valid_risk
	input.risk_level == "medium"
	input.action_type != "scenario.run"
	input.action_type != "demo_fixture.load"
	input.action_type != "release_baseline.run"
	not scenario_admin_action
	not medium_approval_actions[input.action_type]
	input.action_type != "module.runtime.register"
	not model_action
	not model_gateway_action
	not execution_action
	not capability_runtime_action
	not task_run_action
	not identity_or_scope_action
	not evidence_action
	not mcp_action
	not dialogue_action
	not belief_action
	not scheduler_action
	not incident_action
	not module_binding_action
	not module_activation_action
	not module_mock_action
	not model_provider_hardening_action
	not conformance_action
	not golden_path_action
	not bootstrap_action
	not release_candidate_action
	not security_read_action
	not security_run_action
	not security_admin_action
	not runtime_config_action
	not resilience_action
}

decision := {
	"allow": false,
	"approval_required": true,
	"reason": "elevated_risk_action_requires_approval",
	"constraints": ["approval_required"],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	elevated_risk
	not mcp_action
	input.action_type != "memory.forget.request"
	not input.approval_present
}

decision := {
	"allow": true,
	"approval_required": false,
	"reason": "elevated_risk_action_approved",
	"constraints": [],
	"audit_level": "high",
} if {
	valid_action
	valid_risk
	elevated_risk
	not mcp_action
	input.action_type != "memory.forget.request"
	input.approval_present
}

scheduler_action if {
	startswith(input.action_type, "scheduler.")
}

scheduler_read_action if {
	input.action_type == "scheduler.schedule.read"
}

scheduler_read_action if {
	input.action_type == "scheduler.due_item.read"
}

scheduler_read_action if {
	input.action_type == "scheduler.reminder.read"
}

scheduler_read_action if {
	input.action_type == "scheduler.policy.read"
}

scheduler_read_action if {
	input.action_type == "scheduler.report.read"
}

scheduler_write_action if {
	input.action_type == "scheduler.schedule.create"
}

scheduler_write_action if {
	input.action_type == "scheduler.schedule.update"
}

scheduler_write_action if {
	input.action_type == "scheduler.schedule.delete"
}

scheduler_write_action if {
	input.action_type == "scheduler.due_item.update"
}

scheduler_write_action if {
	input.action_type == "scheduler.reminder.create"
}

scheduler_write_action if {
	input.action_type == "scheduler.reminder.update"
}

scheduler_write_action if {
	input.action_type == "scheduler.policy.create"
}

scheduler_write_action if {
	input.action_type == "scheduler.policy.update"
}

scheduler_write_action if {
	input.action_type == "scheduler.report.create"
}

scheduler_operator if {
	input.context.actor_context.roles[_] == "owner"
}

scheduler_operator if {
	input.context.actor_context.roles[_] == "admin"
}

scheduler_operator if {
	input.context.actor_context.roles[_] == "operator"
}

scheduler_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

scheduler_reader if {
	scheduler_operator
}

scheduler_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

scheduler_reader if {
	input.context.actor_context.permissions[_] == "scheduler.schedule.read"
}

scheduler_reader if {
	input.context.actor_context.permissions[_] == "scheduler.reminder.read"
}

scheduler_writer if {
	scheduler_operator
}

scheduler_external_action if {
	input.context.execute_target == true
}

scheduler_external_action if {
	input.context.external_calendar == true
}

incident_action if {
	startswith(input.action_type, "incident.")
}

incident_read_action if {
	input.action_type == "incident.signal.read"
}

incident_read_action if {
	input.action_type == "incident.rule.read"
}

incident_read_action if {
	input.action_type == "incident.read"
}

incident_read_action if {
	input.action_type == "incident.root_cause.read"
}

incident_read_action if {
	input.action_type == "incident.recovery_review.read"
}

incident_write_action if {
	input.action_type == "incident.signal.create"
}

incident_write_action if {
	input.action_type == "incident.signal.update"
}

incident_write_action if {
	input.action_type == "incident.rule.create"
}

incident_write_action if {
	input.action_type == "incident.rule.update"
}

incident_write_action if {
	input.action_type == "incident.create"
}

incident_write_action if {
	input.action_type == "incident.update"
}

incident_write_action if {
	input.action_type == "incident.delete"
}

incident_write_action if {
	input.action_type == "incident.root_cause.create"
}

incident_write_action if {
	input.action_type == "incident.root_cause.update"
}

incident_write_action if {
	input.action_type == "incident.recovery_review.create"
}

incident_operator if {
	input.context.actor_context.roles[_] == "owner"
}

incident_operator if {
	input.context.actor_context.roles[_] == "admin"
}

incident_operator if {
	input.context.actor_context.roles[_] == "operator"
}

incident_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

incident_reader if {
	incident_operator
}

incident_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

incident_reader if {
	input.context.actor_context.permissions[_] == "incident.read"
}

incident_reader if {
	input.context.actor_context.permissions[_] == "incident.signal.read"
}

incident_external_action if {
	input.context.source_records_mutated == true
}

incident_external_action if {
	input.context.remediation_execution == true
}

incident_external_action if {
	input.context.execute_remediation == true
}

valid_action if {
	allowed_actions[input.action_type]
}

valid_risk if {
	valid_risks[input.risk_level]
}

valid_runtime_type if {
	valid_runtime_types[input.context.runtime_type]
}

non_executable_runtime_type if {
	input.context.runtime_type == "http"
}

non_executable_runtime_type if {
	input.context.runtime_type == "mcp"
}

elevated_risk if {
	input.risk_level == "high"
}

elevated_risk if {
	input.risk_level == "critical"
}

low_or_medium_risk if {
	input.risk_level == "low"
}

low_or_medium_risk if {
	input.risk_level == "medium"
}

model_action if {
	input.action_type == "model.route"
}

model_action if {
	input.action_type == "model.complete"
}

model_gateway_action if {
	input.action_type == "model.gateway.complete"
}

local_model_provider if {
	input.context.selected_provider == "aion-local"
}

local_model_provider if {
	input.context.selected_provider == "deterministic"
}

external_model_allowed if {
	input.context.allow_external == true
	input.context.model_gateway_enabled == true
	input.context.actor_context.permissions[_] == "model.external.use"
}

model_read_action if {
	input.action_type == "model.provider.read"
}

model_read_action if {
	input.action_type == "model.profile.read"
}

model_read_action if {
	input.action_type == "model.usage.read"
}

model_read_action if {
	input.action_type == "model.budget.read"
}

model_admin_action if {
	input.action_type == "model.provider.register"
}

model_admin_action if {
	input.action_type == "model.provider.disable"
}

model_admin_action if {
	input.action_type == "model.provider.health_check"
}

model_admin_action if {
	input.action_type == "model.profile.register"
}

model_admin_action if {
	input.action_type == "model.profile.disable"
}

model_budget_write_action if {
	input.action_type == "model.budget.create"
}

model_budget_write_action if {
	input.action_type == "model.budget.update"
}

execution_action if {
	input.action_type == "plan.execute"
}

execution_action if {
	input.action_type == "execution.step"
}

capability_runtime_action if {
	input.action_type == "capability.invoke"
}

task_run_action if {
	input.action_type == "task.run"
}

identity_or_scope_action if {
	identity_action
}

identity_or_scope_action if {
	scope_action
}

evidence_action if {
	input.action_type == "evidence.create"
}

visual_or_observability_action if {
	startswith(input.action_type, "visual.")
}

visual_or_observability_action if {
	startswith(input.action_type, "observability.")
}

lifecycle_action if {
	startswith(input.action_type, "lifecycle.")
}

lifecycle_read_action if {
	input.action_type == "lifecycle.policy.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.classification.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.archive_candidate.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.redaction_candidate.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.purge_preview.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.review.read"
}

lifecycle_read_action if {
	input.action_type == "lifecycle.report.read"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.policy.create"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.policy.update"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.classify"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.evaluate"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.archive_candidate.create"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.archive_candidate.update"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.redaction_candidate.create"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.redaction_candidate.update"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.purge_preview.create"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.review.create"
}

lifecycle_advisory_action if {
	input.action_type == "lifecycle.report.create"
}

lifecycle_hard_delete_requested if {
	input.context.hard_delete_allowed == true
}

lifecycle_hard_delete_requested if {
	input.context.hard_delete_enabled == true
}

dialogue_action if {
	startswith(input.action_type, "dialogue.")
}

dialogue_controlled_mode if {
	input.action_type == "dialogue.turn"
	input.context.mode == "controlled"
}

belief_action if {
	startswith(input.action_type, "belief.")
}

registry_action if {
	startswith(input.action_type, "concept.")
}

registry_action if {
	startswith(input.action_type, "entity.")
}

registry_action if {
	startswith(input.action_type, "situation.")
}

registry_action if {
	startswith(input.action_type, "decision.")
}

registry_action if {
	startswith(input.action_type, "outcome.")
}

registry_action if {
	startswith(input.action_type, "registry.")
}

contract_registry_action if {
	startswith(input.action_type, "contract_registry.")
}

extension_registry_action if {
	startswith(input.action_type, "extension.")
}

module_binding_action if {
	startswith(input.action_type, "module_slot.")
}

module_binding_action if {
	startswith(input.action_type, "capability_binding.")
}

module_binding_action if {
	startswith(input.action_type, "module_binding.")
}

module_binding_action if {
	startswith(input.action_type, "module_mount_plan.")
}

module_binding_action if {
	startswith(input.action_type, "route_binding_preview.")
}

module_activation_action if {
	startswith(input.action_type, "module_activation.")
}

module_activation_action if {
	startswith(input.action_type, "runtime.registration.preview.")
}

module_mock_action if {
	startswith(input.action_type, "module_mock.")
}

model_provider_hardening_action if {
	startswith(input.action_type, "model_provider.")
}

contract_registry_read_action if {
	input.action_type == "contract_registry.resource.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.interface.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.snapshot.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.rule.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.finding.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.migration_note.read"
}

contract_registry_read_action if {
	input.action_type == "contract_registry.report.read"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.resource.create"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.resource.update"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.snapshot.create"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.rule.create"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.rule.update"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.compatibility.scan"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.finding.update"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.migration_note.create"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.migration_note.update"
}

contract_registry_advisory_action if {
	input.action_type == "contract_registry.report.create"
}

contract_registry_source_mutation_requested if {
	input.context.source_mutated == true
}

contract_registry_source_mutation_requested if {
	input.context.source_mutation_requested == true
}

contract_registry_source_mutation_requested if {
	input.context.code_generated == true
}

extension_registry_read_action if {
	input.action_type == "extension.package.read"
}

extension_registry_read_action if {
	input.action_type == "extension.manifest.validate"
}

extension_registry_read_action if {
	input.action_type == "extension.dependency.read"
}

extension_registry_read_action if {
	input.action_type == "extension.capability_declaration.read"
}

extension_registry_read_action if {
	input.action_type == "extension.install_plan.read"
}

extension_registry_read_action if {
	input.action_type == "extension.query"
}

extension_registry_metadata_action if {
	input.action_type == "extension.package.create"
}

extension_registry_metadata_action if {
	input.action_type == "extension.package.update"
}

extension_registry_metadata_action if {
	input.action_type == "extension.package.delete"
}

extension_registry_metadata_action if {
	input.action_type == "extension.compatibility.check"
}

extension_registry_metadata_action if {
	input.action_type == "extension.intake"
}

extension_registry_metadata_action if {
	input.action_type == "extension.review"
}

extension_registry_metadata_action if {
	input.action_type == "extension.install_plan.create"
}

extension_registry_metadata_action if {
	input.action_type == "extension.install_plan.update"
}

extension_unsafe_request if {
	input.context.source_mutated == true
}

extension_unsafe_request if {
	input.context.source_mutation_requested == true
}

extension_unsafe_request if {
	input.context.code_loading_requested == true
}

extension_unsafe_request if {
	input.context.activation_requested == true
}

extension_unsafe_request if {
	input.context.external_sources_requested == true
}

extension_unsafe_request if {
	input.context.code_generated == true
}

module_binding_read_action if {
	input.action_type == "module_slot.read"
}

module_binding_read_action if {
	input.action_type == "capability_binding.read"
}

module_binding_read_action if {
	input.action_type == "module_binding.conflict.read"
}

module_binding_read_action if {
	input.action_type == "module_mount_plan.read"
}

module_binding_read_action if {
	input.action_type == "route_binding_preview.read"
}

module_binding_read_action if {
	input.action_type == "module_binding.query"
}

module_binding_metadata_action if {
	input.action_type == "module_slot.create"
}

module_binding_metadata_action if {
	input.action_type == "module_slot.update"
}

module_binding_metadata_action if {
	input.action_type == "module_slot.delete"
}

module_binding_metadata_action if {
	input.action_type == "capability_binding.create"
}

module_binding_metadata_action if {
	input.action_type == "capability_binding.update"
}

module_binding_metadata_action if {
	input.action_type == "module_binding.validate"
}

module_binding_metadata_action if {
	input.action_type == "module_binding.conflict.update"
}

module_binding_metadata_action if {
	input.action_type == "module_mount_plan.create"
}

module_binding_metadata_action if {
	input.action_type == "module_mount_plan.update"
}

module_binding_metadata_action if {
	input.action_type == "route_binding_preview.create"
}

module_binding_unsafe_request if {
	input.context.source_mutated == true
}

module_binding_unsafe_request if {
	input.context.source_mutation_requested == true
}

module_binding_unsafe_request if {
	input.context.code_loading_requested == true
}

module_binding_unsafe_request if {
	input.context.activation_requested == true
}

module_binding_unsafe_request if {
	input.context.capability_execution_requested == true
}

module_binding_unsafe_request if {
	input.context.dynamic_route_registration_requested == true
}

module_binding_unsafe_request if {
	input.context.external_source_requested == true
}

module_binding_unsafe_request if {
	input.context.shell_command_requested == true
}

module_binding_unsafe_request if {
	input.context.code_generated == true
}

module_activation_read_action if {
	input.action_type == "module_activation.request.read"
}

module_activation_read_action if {
	input.action_type == "module_activation.gate.read"
}

module_activation_read_action if {
	input.action_type == "module_activation.blocker.read"
}

module_activation_read_action if {
	input.action_type == "module_activation.review.read"
}

module_activation_read_action if {
	input.action_type == "module_activation.plan.read"
}

module_activation_read_action if {
	input.action_type == "module_activation.query.read"
}

module_activation_read_action if {
	input.action_type == "runtime.registration.preview.read"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.request.create"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.request.update"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.request.delete"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.gate.run"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.blocker.update"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.review.create"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.plan.create"
}

module_activation_metadata_action if {
	input.action_type == "module_activation.plan.update"
}

module_activation_metadata_action if {
	input.action_type == "runtime.registration.preview.create"
}

module_activation_unsafe_request if {
	input.context.source_mutated == true
}

module_activation_unsafe_request if {
	input.context.source_mutation_requested == true
}

module_activation_unsafe_request if {
	input.context.code_loading_requested == true
}

module_activation_unsafe_request if {
	input.context.activation_requested == true
}

module_activation_unsafe_request if {
	input.context.activation_performed == true
}

module_activation_unsafe_request if {
	input.context.capability_execution_requested == true
}

module_activation_unsafe_request if {
	input.context.runtime_registration_requested == true
}

module_activation_unsafe_request if {
	input.context.dynamic_route_registration_requested == true
}

module_activation_unsafe_request if {
	input.context.external_call_requested == true
}

module_activation_unsafe_request if {
	input.context.shell_command_requested == true
}

module_activation_unsafe_request if {
	input.context.code_generated == true
}

module_mock_read_action if {
	input.action_type == "module_mock.profile.read"
}

module_mock_read_action if {
	input.action_type == "module_mock.run.read"
}

module_mock_read_action if {
	input.action_type == "module_mock.output.read"
}

module_mock_read_action if {
	input.action_type == "module_mock.finding.read"
}

module_mock_read_action if {
	input.action_type == "module_mock.query"
}

module_mock_metadata_action if {
	input.action_type == "module_mock.profile.create"
}

module_mock_metadata_action if {
	input.action_type == "module_mock.profile.update"
}

module_mock_metadata_action if {
	input.action_type == "module_mock.invoke"
}

module_mock_metadata_action if {
	input.action_type == "module_mock.finding.update"
}

module_mock_unsafe_request if {
	input.context.source_mutated == true
}

module_mock_unsafe_request if {
	input.context.source_mutation_requested == true
}

module_mock_unsafe_request if {
	input.context.code_loading_requested == true
}

module_mock_unsafe_request if {
	input.context.package_install_requested == true
}

module_mock_unsafe_request if {
	input.context.activation_requested == true
}

module_mock_unsafe_request if {
	input.context.activation_allowed == true
}

module_mock_unsafe_request if {
	input.context.capability_execution_requested == true
}

module_mock_unsafe_request if {
	input.context.execution_allowed == true
}

module_mock_unsafe_request if {
	input.context.external_call_requested == true
}

module_mock_unsafe_request if {
	input.context.external_calls_made == true
}

module_mock_unsafe_request if {
	input.context.dynamic_route_registration_requested == true
}

module_mock_unsafe_request if {
	input.context.shell_command_requested == true
}

module_mock_unsafe_request if {
	input.context.code_generated == true
}

model_provider_read_action if {
	input.action_type == "model_provider.profile.read"
}

model_provider_read_action if {
	input.action_type == "model_provider.blocker.read"
}

model_provider_read_action if {
	input.action_type == "model_provider.query"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.profile.create"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.profile.update"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.egress.preview"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.simulate"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.readiness.assess"
}

model_provider_metadata_action if {
	input.action_type == "model_provider.blocker.update"
}

model_provider_unsafe_request if {
	input.context.external_call_requested == true
}

model_provider_unsafe_request if {
	input.context.external_calls_made == true
}

model_provider_unsafe_request if {
	input.context.external_model_calls_enabled == true
}

model_provider_unsafe_request if {
	input.context.credentials_used == true
}

model_provider_unsafe_request if {
	input.context.credentials_enabled == true
}

model_provider_unsafe_request if {
	input.context.model_invoked == true
}

model_provider_unsafe_request if {
	input.context.provider_enabled == true
}

model_provider_unsafe_request if {
	input.context.tool_execution_requested == true
}

model_provider_unsafe_request if {
	input.context.raw_prompt_included == true
}

conformance_action if {
	startswith(input.action_type, "conformance.")
}

conformance_read_action if {
	input.action_type == "conformance.profile.read"
}

conformance_read_action if {
	input.action_type == "conformance.test_vector.read"
}

conformance_read_action if {
	input.action_type == "conformance.finding.read"
}

conformance_read_action if {
	input.action_type == "conformance.readiness.read"
}

conformance_read_action if {
	input.action_type == "conformance.query"
}

conformance_metadata_action if {
	input.action_type == "conformance.profile.create"
}

conformance_metadata_action if {
	input.action_type == "conformance.profile.update"
}

conformance_metadata_action if {
	input.action_type == "conformance.test_vector.create"
}

conformance_metadata_action if {
	input.action_type == "conformance.test_vector.update"
}

conformance_metadata_action if {
	input.action_type == "conformance.run"
}

conformance_metadata_action if {
	input.action_type == "conformance.finding.update"
}

conformance_metadata_action if {
	input.action_type == "conformance.readiness.assess"
}

conformance_unsafe_request if {
	input.context.source_mutated == true
}

conformance_unsafe_request if {
	input.context.source_mutation_requested == true
}

conformance_unsafe_request if {
	input.context.code_loading_requested == true
}

conformance_unsafe_request if {
	input.context.package_install_requested == true
}

conformance_unsafe_request if {
	input.context.activation_requested == true
}

conformance_unsafe_request if {
	input.context.capability_execution_requested == true
}

conformance_unsafe_request if {
	input.context.external_call_requested == true
}

conformance_unsafe_request if {
	input.context.external_source_requested == true
}

conformance_unsafe_request if {
	input.context.dynamic_route_registration_requested == true
}

conformance_unsafe_request if {
	input.context.shell_command_requested == true
}

conformance_unsafe_request if {
	input.context.code_generated == true
}

golden_path_action if {
	startswith(input.action_type, "golden_path.")
}

golden_path_read_action if {
	input.action_type == "golden_path.scenario.read"
}

golden_path_read_action if {
	input.action_type == "golden_path.fixture.read"
}

golden_path_read_action if {
	input.action_type == "golden_path.run.read"
}

golden_path_read_action if {
	input.action_type == "golden_path.report.read"
}

golden_path_read_action if {
	input.action_type == "golden_path.query"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.scenario.create"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.fixture.create"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.run"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.assertion.evaluate"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.report.create"
}

golden_path_metadata_action if {
	input.action_type == "golden_path.release_smoke.run"
}

golden_path_unsafe_request if {
	input.context.external_calls == true
}

golden_path_unsafe_request if {
	input.context.external_call_requested == true
}

golden_path_unsafe_request if {
	input.context.tool_execution == true
}

golden_path_unsafe_request if {
	input.context.tool_execution_requested == true
}

golden_path_unsafe_request if {
	input.context.shell_execution == true
}

golden_path_unsafe_request if {
	input.context.shell_command_requested == true
}

golden_path_unsafe_request if {
	input.context.code_generated == true
}

golden_path_unsafe_request if {
	input.context.source_records_mutated == true
}

golden_path_unsafe_request if {
	input.context.source_mutation_requested == true
}

bootstrap_action if {
	startswith(input.action_type, "bootstrap.")
}

bootstrap_read_action if {
	input.action_type == "bootstrap.profile.read"
}

bootstrap_read_action if {
	input.action_type == "bootstrap.seed_bundle.read"
}

bootstrap_read_action if {
	input.action_type == "bootstrap.finding.read"
}

bootstrap_read_action if {
	input.action_type == "bootstrap.run.read"
}

bootstrap_read_action if {
	input.action_type == "bootstrap.report.read"
}

bootstrap_read_action if {
	input.action_type == "bootstrap.query"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.profile.create"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.profile.update"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.seed_bundle.create"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.seed_bundle.update"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.seed.execute"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.doctor.run"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.finding.update"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.run"
}

bootstrap_metadata_action if {
	input.action_type == "bootstrap.report.create"
}

bootstrap_mode_allowed if {
	not input.context.mode
}

bootstrap_mode_allowed if {
	input.context.mode == "dry_run"
}

bootstrap_mode_allowed if {
	input.context.mode == "controlled"
	input.context.safe_local_defaults == true
}

bootstrap_mode_allowed if {
	input.context.mode == "controlled"
	input.context.allow_local_defaults == true
}

bootstrap_unsafe_request if {
	input.context.external_calls == true
}

bootstrap_unsafe_request if {
	input.context.external_call_requested == true
}

bootstrap_unsafe_request if {
	input.context.external_provider_enabled == true
}

bootstrap_unsafe_request if {
	input.context.external_features_enabled == true
}

bootstrap_unsafe_request if {
	input.context.package_install == true
}

bootstrap_unsafe_request if {
	input.context.package_install_requested == true
}

bootstrap_unsafe_request if {
	input.context.production_secret_created == true
}

bootstrap_unsafe_request if {
	input.context.production_auth_enabled == true
}

bootstrap_unsafe_request if {
	input.context.full_autonomy_enabled == true
}

bootstrap_unsafe_request if {
	input.context.code_loading_enabled == true
}

bootstrap_unsafe_request if {
	input.context.tool_execution == true
}

bootstrap_unsafe_request if {
	input.context.shell_execution == true
}

bootstrap_unsafe_request if {
	input.context.source_records_mutated == true
}

bootstrap_unsafe_request if {
	input.context.source_mutation_requested == true
}

bootstrap_unsafe_request if {
	input.context.hard_delete_enabled == true
}

release_candidate_action if {
	startswith(input.action_type, "release_candidate.")
}

release_candidate_read_action if {
	input.action_type == "release_candidate.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.matrix.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.run.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.finding.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.evidence_pack.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.report.read"
}

release_candidate_read_action if {
	input.action_type == "release_candidate.query"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.create"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.update"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.matrix.create"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.matrix.update"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.gate.run"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.finding.update"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.evidence_pack.create"
}

release_candidate_metadata_action if {
	input.action_type == "release_candidate.report.create"
}

release_candidate_mode_allowed if {
	not input.context.mode
}

release_candidate_mode_allowed if {
	input.context.mode == "dry_run"
}

release_candidate_mode_allowed if {
	input.context.mode == "controlled"
	input.context.controlled_records == "rc_owned_only"
}

release_candidate_unsafe_request if {
	input.context.external_calls == true
}

release_candidate_unsafe_request if {
	input.context.external_call_requested == true
}

release_candidate_unsafe_request if {
	input.context.deployment == true
}

release_candidate_unsafe_request if {
	input.context.deploy_requested == true
}

release_candidate_unsafe_request if {
	input.context.publish == true
}

release_candidate_unsafe_request if {
	input.context.publish_requested == true
}

release_candidate_unsafe_request if {
	input.context.source_mutation == true
}

release_candidate_unsafe_request if {
	input.context.source_mutation_requested == true
}

release_candidate_unsafe_request if {
	input.context.source_records_mutated == true
}

release_candidate_unsafe_request if {
	input.context.enable_disabled_features == true
}

release_candidate_unsafe_request if {
	input.context.code_loading_enabled == true
}

release_candidate_unsafe_request if {
	input.context.full_autonomy_enabled == true
}

registry_approval_action if {
	input.action_type == "entity.merge.approve"
}

registry_approval_action if {
	input.action_type == "entity.split.approve"
}

belief_read_action if {
	input.action_type == "belief.claim.read"
}

belief_read_action if {
	input.action_type == "belief.support.read"
}

belief_read_action if {
	input.action_type == "belief.contradiction.read"
}

belief_read_action if {
	input.action_type == "belief.query"
}

belief_mutation_action if {
	input.action_type == "belief.claim.update"
}

belief_mutation_action if {
	input.action_type == "belief.claim.delete"
}

belief_mutation_action if {
	input.action_type == "belief.support.delete"
}

belief_mutation_action if {
	input.action_type == "belief.contradiction.create"
}

belief_mutation_action if {
	input.action_type == "belief.contradiction.resolve"
}

belief_internal_or_admin if {
	admin_or_owner
}

belief_internal_or_admin if {
	input.context.source == "internal_brain_service"
}

belief_internal_or_admin if {
	input.context.actor_context.roles[_] == "system"
}

belief_operator if {
	admin_or_owner
}

belief_operator if {
	input.context.actor_context.roles[_] == "operator"
}

security_action if {
	startswith(input.action_type, "security.")
}

runtime_config_action if {
	startswith(input.action_type, "runtime_config.")
}

resilience_action if {
	startswith(input.action_type, "resilience.")
}

audit_action if {
	startswith(input.action_type, "audit.")
}

mcp_action if {
	startswith(input.action_type, "mcp.")
}

api_support_action if {
	startswith(input.action_type, "api.")
}

scenario_admin_action if {
	input.action_type == "scenario.create"
}

scenario_admin_action if {
	input.action_type == "scenario.disable"
}

scenario_admin_action if {
	input.action_type == "scenario.seed_defaults"
}

mcp_read_action if {
	input.action_type == "mcp.server.read"
}

mcp_read_action if {
	input.action_type == "mcp.server.health_check"
}

mcp_read_action if {
	input.action_type == "mcp.mapping.read"
}

mcp_admin_action if {
	input.action_type == "mcp.server.register"
}

mcp_admin_action if {
	input.action_type == "mcp.server.disable"
}

mcp_admin_action if {
	input.action_type == "mcp.tools.sync"
}

mcp_admin_action if {
	input.action_type == "mcp.mapping.write"
}

mcp_reader if {
	dev_owner
}

mcp_reader if {
	input.context.actor_context.permissions[_] == "mcp.server.read"
}

mcp_reader if {
	input.context.actor_context.permissions[_] == "mcp.mapping.read"
}

mcp_reader if {
	input.context.permissions[_] == input.action_type
}

mcp_operator if {
	dev_owner
}

mcp_operator if {
	admin_or_owner
}

mcp_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

mcp_operator if {
	input.context.permissions[_] == input.action_type
}

module_developer_operator if {
	dev_owner
}

module_developer_operator if {
	admin_or_owner
}

module_developer_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

module_developer_operator if {
	input.context.permissions[_] == input.action_type
}

mcp_invoke_permission if {
	dev_owner
}

mcp_invoke_permission if {
	input.context.actor_context.permissions[_] == "capability.invoke"
}

mcp_invoke_permission if {
	input.context.permissions[_] == "capability.invoke"
}

mcp_transport_allowed if {
	not input.context.transport_type
}

mcp_transport_allowed if {
	input.context.transport_type == "in_memory_fake"
}

mcp_transport_allowed if {
	input.context.transport_type == "http"
	mcp_network_permission
}

mcp_transport_allowed if {
	input.context.transport_type == "sse"
	mcp_network_permission
}

mcp_transport_allowed if {
	input.context.transport_type == "stdio"
	mcp_stdio_permission
}

mcp_network_permission if {
	input.context.actor_context.permissions[_] == "mcp.network.use"
}

mcp_network_permission if {
	input.context.permissions[_] == "mcp.network.use"
}

mcp_stdio_permission if {
	input.context.actor_context.permissions[_] == "mcp.stdio.use"
}

mcp_stdio_permission if {
	input.context.permissions[_] == "mcp.stdio.use"
}

controlled_mcp_risk_requires_approval if {
	input.risk_level == "medium"
}

controlled_mcp_risk_requires_approval if {
	input.risk_level == "high"
}

controlled_mcp_risk_requires_approval if {
	input.risk_level == "critical"
}

mcp_risk_approved if {
	input.risk_level == "low"
}

mcp_risk_approved if {
	controlled_mcp_risk_requires_approval
	input.approval_present
}

kernel_dev_action if {
	input.action_type == "kernel.self_test.run"
}

kernel_dev_action if {
	input.action_type == "kernel.boundary_check.run"
}

kernel_contract_exporter if {
	dev_owner
}

kernel_contract_exporter if {
	input.context.actor_context.permissions[_] == "kernel.contracts.export"
}

visual_read_action if {
	input.action_type == "visual.map.read"
}

visual_read_action if {
	input.action_type == "visual.telemetry.read"
}

visual_read_action if {
	input.action_type == "visual.snapshot.read"
}

visual_read_action if {
	input.action_type == "visual.timeline.read"
}

visual_read_action if {
	input.action_type == "observability.read"
}

grounding_read_action if {
	input.action_type == "grounding.source.read"
}

grounding_read_action if {
	input.action_type == "grounding.citation.read"
}

grounding_read_action if {
	input.action_type == "grounding.coverage.read"
}

grounding_read_action if {
	input.action_type == "grounding.query"
}

grounding_read_action if {
	input.action_type == "grounding.unsupported.read"
}

grounding_read_action if {
	input.action_type == "grounding.map"
}

grounding_write_action if {
	input.action_type == "grounding.source.create"
}

grounding_write_action if {
	input.action_type == "grounding.citation.create"
}

grounding_write_action if {
	input.action_type == "grounding.citation.delete"
}

grounding_read_permission if {
	dev_owner
}

grounding_read_permission if {
	input.context.actor_context.permissions[_] == "trace.read"
}

grounding_read_permission if {
	input.context.actor_context.permissions[_] == "grounding.read"
}

grounding_writer if {
	dev_owner
}

grounding_writer if {
	input.context.actor_context.actor_type == "system"
}

grounding_writer if {
	input.context.actor_context.permissions[_] == "grounding.write"
}

grounding_verifier if {
	dev_owner
}

grounding_verifier if {
	input.context.actor_context.permissions[_] == "grounding.verify"
}

grounding_verifier if {
	input.context.actor_context.permissions[_] == "operator"
}

visual_read_permission if {
	input.context.actor_context.permissions[_] == "trace.read"
}

visual_read_permission if {
	input.context.actor_context.permissions[_] == "telemetry.read"
}

visual_stream_permission if {
	input.context.actor_context.permissions[_] == "visual.stream.read"
}

visual_snapshot_create_permission if {
	input.context.actor_context.permissions[_] == "visual.snapshot.create"
}

observability_writer if {
	dev_owner
}

contract_registry_permission if {
	dev_owner
}

contract_registry_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

contract_registry_permission if {
	input.context.permissions[_] == input.action_type
}

contract_registry_permission if {
	input.context.actor_context.permissions[_] == "contract_registry.read"
	contract_registry_read_action
}

contract_registry_permission if {
	input.context.actor_context.permissions[_] == "contract_registry.write"
	contract_registry_advisory_action
}

contract_registry_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

extension_registry_permission if {
	dev_owner
}

extension_registry_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

extension_registry_permission if {
	input.context.permissions[_] == input.action_type
}

extension_registry_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

extension_registry_permission if {
	input.context.actor_context.permissions[_] == "extension.read"
	extension_registry_read_action
}

extension_registry_permission if {
	input.context.actor_context.permissions[_] == "extension.write"
	extension_registry_metadata_action
}

extension_registry_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

module_binding_permission if {
	dev_owner
}

module_binding_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

module_binding_permission if {
	input.context.permissions[_] == input.action_type
}

module_binding_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

module_binding_permission if {
	input.context.actor_context.permissions[_] == "module_binding.read"
	module_binding_read_action
}

module_binding_permission if {
	input.context.actor_context.permissions[_] == "module_binding.write"
	module_binding_metadata_action
}

module_binding_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

module_activation_permission if {
	dev_owner
}

module_activation_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

module_activation_permission if {
	input.context.permissions[_] == input.action_type
}

module_activation_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

module_activation_permission if {
	input.context.actor_context.permissions[_] == "module_activation.read"
	module_activation_read_action
}

module_activation_permission if {
	input.context.actor_context.permissions[_] == "module_activation.write"
	module_activation_metadata_action
}

module_activation_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

module_mock_permission if {
	dev_owner
}

module_mock_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

module_mock_permission if {
	input.context.permissions[_] == input.action_type
}

module_mock_permission if {
	module_mock_read_action
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

module_mock_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

module_mock_permission if {
	input.context.actor_context.permissions[_] == "module_mock.read"
	module_mock_read_action
}

module_mock_permission if {
	input.context.actor_context.permissions[_] == "module_mock.write"
	module_mock_metadata_action
}

module_mock_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

model_provider_permission if {
	dev_owner
}

model_provider_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

model_provider_permission if {
	input.context.permissions[_] == input.action_type
}

model_provider_permission if {
	model_provider_read_action
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

model_provider_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

model_provider_permission if {
	input.context.actor_context.permissions[_] == "model_provider.read"
	model_provider_read_action
}

model_provider_permission if {
	input.context.actor_context.permissions[_] == "model_provider.write"
	model_provider_metadata_action
}

model_provider_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

conformance_permission if {
	dev_owner
}

conformance_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

conformance_permission if {
	input.context.permissions[_] == input.action_type
}

conformance_permission if {
	conformance_read_action
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

conformance_permission if {
	input.actor_id
	input.requested_permissions[_] == input.action_type
	input.security_scope[_] == sprintf("workspace:%s", [input.workspace_id])
}

conformance_permission if {
	input.context.actor_context.permissions[_] == "conformance.read"
	conformance_read_action
}

conformance_permission if {
	input.context.actor_context.permissions[_] == "conformance.write"
	conformance_metadata_action
}

conformance_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

golden_path_permission if {
	dev_owner
}

golden_path_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

golden_path_permission if {
	input.context.permissions[_] == input.action_type
}

golden_path_permission if {
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

golden_path_permission if {
	input.context.actor_context.permissions[_] == "golden_path.read"
	golden_path_read_action
}

golden_path_permission if {
	input.context.actor_context.permissions[_] == "golden_path.write"
	golden_path_metadata_action
}

golden_path_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

bootstrap_permission if {
	dev_owner
}

bootstrap_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

bootstrap_permission if {
	input.context.permissions[_] == input.action_type
}

bootstrap_permission if {
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

bootstrap_permission if {
	input.context.actor_context.permissions[_] == "bootstrap.read"
	bootstrap_read_action
}

bootstrap_permission if {
	input.context.actor_context.permissions[_] == "bootstrap.write"
	bootstrap_metadata_action
}

bootstrap_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

bootstrap_permission if {
	input.context.actor_context.roles[_] == "auditor"
	bootstrap_read_action
}

release_candidate_permission if {
	dev_owner
}

release_candidate_permission if {
	admin_or_owner
}

release_candidate_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

release_candidate_permission if {
	input.context.permissions[_] == input.action_type
}

release_candidate_permission if {
	input.requested_permissions[_] == input.action_type
	count(input.security_scope) > 0
}

release_candidate_permission if {
	input.context.actor_context.permissions[_] == "release_candidate.read"
	release_candidate_read_action
}

release_candidate_permission if {
	input.context.actor_context.permissions[_] == "release_candidate.write"
	release_candidate_metadata_action
}

release_candidate_permission if {
	input.context.actor_context.permissions[_] == "operator"
}

release_candidate_permission if {
	input.context.actor_context.roles[_] == "auditor"
	release_candidate_read_action
}

lifecycle_permission if {
	dev_owner
}

lifecycle_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

lifecycle_permission if {
	input.context.permissions[_] == input.action_type
}

lifecycle_permission if {
	input.context.actor_context.permissions[_] == "lifecycle.read"
	lifecycle_read_action
}

lifecycle_permission if {
	input.context.actor_context.permissions[_] == "lifecycle.write"
	lifecycle_advisory_action
}

prompt_action if {
	startswith(input.action_type, "prompt.")
}

prompt_read_action if {
	input.action_type == "prompt.template.read"
}

prompt_read_action if {
	input.action_type == "prompt.fragment.read"
}

prompt_read_action if {
	input.action_type == "prompt.packet.read"
}

prompt_read_action if {
	input.action_type == "prompt.injection.read"
}

prompt_read_action if {
	input.action_type == "prompt.preview"
}

prompt_read_action if {
	input.action_type == "prompt.manifest.read"
}

prompt_write_action if {
	input.action_type == "prompt.template.create"
}

prompt_write_action if {
	input.action_type == "prompt.template.update"
}

prompt_write_action if {
	input.action_type == "prompt.fragment.create"
}

prompt_write_action if {
	input.action_type == "prompt.fragment.update"
}

prompt_write_action if {
	input.action_type == "prompt.packet.delete"
}

prompt_write_action if {
	input.action_type == "prompt.boundary.check"
}

prompt_write_action if {
	input.action_type == "prompt.manifest.create"
}

prompt_read_permission if {
	dev_owner
}

prompt_read_permission if {
	input.context.actor_context.permissions[_] == input.action_type
}

prompt_read_permission if {
	input.context.actor_context.permissions[_] == "trace.read"
}

prompt_writer if {
	dev_owner
}

prompt_writer if {
	input.context.actor_context.actor_type == "system"
}

prompt_writer if {
	input.context.actor_context.permissions[_] == input.action_type
}

security_read_action if {
	input.action_type == "security.scan.read"
}

security_read_action if {
	input.action_type == "security.threat_model.read"
}

security_read_action if {
	input.action_type == "security.control.read"
}

security_read_action if {
	input.action_type == "security.hardening.read"
}

security_run_action if {
	input.action_type == "security.scan.run"
}

security_run_action if {
	input.action_type == "security.hardening.run"
}

security_admin_action if {
	input.action_type == "security.threat_model.create"
}

security_admin_action if {
	input.action_type == "security.threat_model.update"
}

security_admin_action if {
	input.action_type == "security.control.create"
}

security_admin_action if {
	input.action_type == "security.control.update"
}

runtime_config_read_action if {
	input.action_type == "runtime_config.profile.read"
}

runtime_config_read_action if {
	input.action_type == "runtime_config.feature_override.read"
}

runtime_config_read_action if {
	input.action_type == "runtime_config.snapshot.read"
}

runtime_config_read_action if {
	input.action_type == "runtime_config.status.read"
}

runtime_config_read_action if {
	input.action_type == "runtime_config.change.read"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.profile.create"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.profile.update"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.feature_override.create"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.feature_override.update"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.snapshot.create"
}

runtime_config_write_action if {
	input.action_type == "runtime_config.validate"
}

resilience_read_action if {
	input.action_type == "resilience.status.read"
}

resilience_read_action if {
	input.action_type == "resilience.dependency.check"
}

resilience_read_action if {
	input.action_type == "resilience.dependency.read"
}

resilience_read_action if {
	input.action_type == "resilience.retry_policy.read"
}

resilience_read_action if {
	input.action_type == "resilience.circuit_breaker.read"
}

resilience_read_action if {
	input.action_type == "resilience.degraded.read"
}

resilience_read_action if {
	input.action_type == "resilience.fault_rule.read"
}

resilience_read_action if {
	input.action_type == "resilience.test.read"
}

resilience_write_action if {
	input.action_type == "resilience.retry_policy.create"
}

resilience_write_action if {
	input.action_type == "resilience.retry_policy.update"
}

resilience_write_action if {
	input.action_type == "resilience.circuit_breaker.create"
}

resilience_write_action if {
	input.action_type == "resilience.circuit_breaker.update"
}

resilience_write_action if {
	input.action_type == "resilience.degraded.resolve"
}

resilience_fault_rule_write_action if {
	input.action_type == "resilience.fault_rule.create"
}

resilience_fault_rule_write_action if {
	input.action_type == "resilience.fault_rule.update"
}

resilience_reader if {
	runtime_config_reader
}

resilience_operator if {
	admin_or_owner
}

resilience_operator if {
	input.context.actor_context.roles[_] == "operator"
}

resilience_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

audit_read_action if {
	input.action_type == "audit.entry.read"
}

audit_read_action if {
	input.action_type == "audit.verify"
}

audit_read_action if {
	input.action_type == "audit.checkpoint.read"
}

audit_read_action if {
	input.action_type == "audit.provenance.read"
}

audit_read_action if {
	input.action_type == "audit.status.read"
}

audit_write_action if {
	input.action_type == "audit.entry.write"
}

audit_write_action if {
	input.action_type == "audit.checkpoint.create"
}

audit_write_action if {
	input.action_type == "audit.provenance.write"
}

audit_reader if {
	dev_owner
}

audit_reader if {
	admin_or_owner
}

audit_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

audit_reader if {
	input.context.actor_context.permissions[_] == input.action_type
}

audit_reader if {
	input.context.permissions[_] == input.action_type
}

audit_writer if {
	dev_owner
}

audit_writer if {
	admin_or_owner
}

audit_writer if {
	input.context.actor_context.permissions[_] == input.action_type
}

audit_writer if {
	input.context.permissions[_] == input.action_type
}

operator_read_action if {
	input.action_type == "operator.overview.read"
}

operator_read_action if {
	input.action_type == "operator.cards.read"
}

operator_read_action if {
	input.action_type == "operator.queues.read"
}

operator_read_action if {
	input.action_type == "operator.actions.read"
}

operator_read_action if {
	input.action_type == "operator.acknowledgement.read"
}

operator_read_action if {
	input.action_type == "operator.snapshot.read"
}

operator_read_action if {
	input.action_type == "operator.readiness.read"
}

operator_read_action if {
	input.action_type == "operator.runbooks.read"
}

operator_read_action if {
	input.action_type == "operator_console.view.read"
}

operator_read_action if {
	input.action_type == "operator_console.workflow.read"
}

operator_read_action if {
	input.action_type == "operator_console.action.describe"
}

operator_read_action if {
	input.action_type == "operator_console.query"
}

local_auth_read_action if {
	input.action_type == "local_auth.roles.read"
}

local_auth_read_action if {
	input.action_type == "local_auth.role_matrix.read"
}

local_auth_read_action if {
	input.action_type == "local_auth.status.read"
}

local_session_read_action if {
	input.action_type == "local_session.status.read"
}

local_session_read_action if {
	input.action_type == "local_session.context.read"
}

local_session_boundary_action if {
	input.action_type == "local_session.boundary.check"
}

local_session_boundary_action if {
	input.action_type == "local_session.audit.run"
}

action_authorization_action if {
	input.action_type == "action_authorization.dry_run.authorize"
}

action_authorization_action if {
	input.action_type == "action_authorization.audit.run"
}

action_authorization_action if {
	input.action_type == "action_authorization.decision.read"
}

operator_action_read if {
	input.action_type == "operator_action.request.read"
}

operator_action_read if {
	input.action_type == "operator_action.preview.read"
}

operator_action_read if {
	input.action_type == "operator_action.blocker.read"
}

operator_action_read if {
	input.action_type == "operator_action.query"
}

operator_action_write if {
	input.action_type == "operator_action.request.create"
}

operator_action_write if {
	input.action_type == "operator_action.request.update"
}

operator_action_write if {
	input.action_type == "operator_action.preview.create"
}

operator_action_write if {
	input.action_type == "operator_action.blocker.update"
}

operator_action_write if {
	input.action_type == "operator_action.review"
}

operator_console_auditor if {
	dev_owner
}

operator_console_auditor if {
	admin_or_owner
}

operator_console_auditor if {
	input.context.actor_context.roles[_] == "operator"
}

operator_console_auditor if {
	input.context.actor_context.roles[_] == "auditor"
}

operator_console_auditor if {
	input.context.actor_context.permissions[_] == input.action_type
}

operator_console_auditor if {
	input.context.permissions[_] == input.action_type
}

local_auth_actor if {
	dev_owner
}

local_auth_actor if {
	admin_or_owner
}

local_auth_actor if {
	input.context.actor_context.roles[_] == "operator"
}

local_auth_actor if {
	input.context.actor_context.roles[_] == "auditor"
}

local_auth_actor if {
	input.context.actor_context.roles[_] == "reviewer"
}

local_auth_actor if {
	input.context.actor_context.permissions[_] == input.action_type
}

local_auth_actor if {
	input.context.permissions[_] == input.action_type
}

local_auth_operator if {
	local_auth_actor
}

local_auth_operator if {
	input.context.actor_context.roles[_] == "operator"
}

local_auth_dev_context if {
	input.context.actor_context.dev_mode == true
}

local_auth_dev_context if {
	development_env
}

local_auth_dev_context if {
	dev_owner
}

local_auth_unsafe_request if {
	input.context.production_auth == true
}

local_auth_unsafe_request if {
	input.context.production_auth_enabled == true
}

local_auth_unsafe_request if {
	input.context.credentials_present == true
}

local_auth_unsafe_request if {
	input.context.auth_credentials_enabled == true
}

local_auth_unsafe_request if {
	input.context.session_present == true
}

local_auth_unsafe_request if {
	input.context.auth_sessions_enabled == true
}

local_auth_unsafe_request if {
	input.context.external_identity_provider_enabled == true
}

local_auth_unsafe_request if {
	input.context.write_actions_enabled == true
}

local_auth_unsafe_request if {
	input.context.execute_allowed == true
}

local_auth_unsafe_request if {
	input.context.activation_allowed == true
}

local_session_unsafe_request if {
	local_auth_unsafe_request
}

local_session_unsafe_request if {
	input.context.production_session == true
}

local_session_unsafe_request if {
	input.context.token_issued == true
}

local_session_unsafe_request if {
	input.context.cookie_issued == true
}

local_session_unsafe_request if {
	input.context.persistent == true
}

local_session_unsafe_request if {
	input.context.external_calls_allowed == true
}

action_authorization_unsafe_request if {
	input.context.write_allowed == true
}

action_authorization_unsafe_request if {
	input.context.execution_allowed == true
}

action_authorization_unsafe_request if {
	input.context.activation_allowed == true
}

action_authorization_unsafe_request if {
	input.context.external_calls_allowed == true
}

action_authorization_unsafe_request if {
	input.context.dry_run_only == false
}

action_authorization_auditor if {
	dev_owner
}

action_authorization_auditor if {
	admin_or_owner
}

action_authorization_auditor if {
	input.context.actor_context.roles[_] == "operator"
}

action_authorization_auditor if {
	input.context.actor_context.roles[_] == "auditor"
}

action_authorization_auditor if {
	input.context.actor_context.roles[_] == "admin"
}

operator_reader if {
	dev_owner
}

operator_reader if {
	admin_or_owner
}

operator_reader if {
	input.context.actor_context.roles[_] == "operator"
}

operator_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

operator_reader if {
	input.context.actor_context.roles[_] == "viewer"
}

operator_reader if {
	input.context.actor_context.permissions[_] == input.action_type
}

operator_reader if {
	input.context.permissions[_] == input.action_type
}

operator_writer if {
	dev_owner
}

operator_writer if {
	admin_or_owner
}

operator_writer if {
	input.context.actor_context.roles[_] == "operator"
}

operator_writer if {
	input.context.actor_context.permissions[_] == input.action_type
}

operator_writer if {
	input.context.permissions[_] == input.action_type
}

operator_snapshot_writer if {
	operator_writer
}

operator_snapshot_writer if {
	input.context.actor_context.roles[_] == "auditor"
}

development_env if {
	input.context.env == "development"
}

development_env if {
	input.context.environment == "development"
}

runtime_config_reader if {
	admin_or_owner
}

runtime_config_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

runtime_config_reader if {
	input.context.actor_context.roles[_] == "viewer"
}

runtime_config_reader if {
	input.context.actor_context.permissions[_] == input.action_type
}

runtime_config_reader if {
	input.context.permissions[_] == input.action_type
}

security_reader if {
	admin_or_owner
}

security_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

security_reader if {
	input.context.actor_context.permissions[_] == input.action_type
}

security_reader if {
	input.context.permissions[_] == input.action_type
}

policy_catalog_read_action if {
	input.action_type == "policy.catalog.read"
}

policy_catalog_read_action if {
	input.action_type == "policy.permission.read"
}

policy_catalog_read_action if {
	input.action_type == "policy.role_template.read"
}

policy_catalog_read_action if {
	input.action_type == "policy.test_case.read"
}

policy_catalog_read_action if {
	input.action_type == "policy.coverage.read"
}

policy_catalog_read_action if {
	input.action_type == "policy.opa.status"
}

policy_catalog_admin_action if {
	input.action_type == "policy.catalog.create"
}

policy_catalog_admin_action if {
	input.action_type == "policy.catalog.update"
}

policy_catalog_admin_action if {
	input.action_type == "policy.permission.create"
}

policy_catalog_admin_action if {
	input.action_type == "policy.permission.update"
}

policy_catalog_admin_action if {
	input.action_type == "policy.role_template.create"
}

policy_catalog_admin_action if {
	input.action_type == "policy.role_template.update"
}

policy_catalog_audit_action if {
	input.action_type == "policy.simulate"
}

policy_catalog_audit_action if {
	input.action_type == "policy.test.run"
}

policy_catalog_audit_action if {
	input.action_type == "policy.bundle.export"
}

policy_catalog_reader if {
	policy_catalog_admin
}

policy_catalog_reader if {
	input.context.actor_context.roles[_] == "auditor"
}

policy_catalog_reader if {
	input.context.actor_context.roles[_] == "viewer"
}

policy_catalog_reader if {
	input.context.actor_context.permissions[_] == input.action_type
}

policy_catalog_reader if {
	input.context.permissions[_] == input.action_type
}

policy_catalog_admin if {
	dev_owner
}

policy_catalog_admin if {
	admin_or_owner
}

policy_catalog_admin if {
	input.context.actor_context.permissions[_] == input.action_type
}

policy_catalog_admin if {
	input.context.permissions[_] == input.action_type
}

policy_catalog_auditor if {
	policy_catalog_admin
}

policy_catalog_auditor if {
	input.context.actor_context.roles[_] == "auditor"
}

policy_catalog_auditor if {
	input.context.actor_context.permissions[_] == input.action_type
}

policy_catalog_auditor if {
	input.context.permissions[_] == input.action_type
}

snapshot_writer if {
	dev_owner
}

snapshot_writer if {
	input.context.actor_context.permissions[_] == "snapshot.create"
}

replay_operator if {
	dev_owner
}

replay_operator if {
	input.context.actor_context.permissions[_] == "replay.run"
}

replay_mode_allowed if {
	input.context.mode == "dry_run"
}

replay_mode_allowed if {
	input.context.mode == "deterministic"
}

regression_action if {
	startswith(input.action_type, "regression.")
}

regression_operator if {
	dev_owner
}

regression_operator if {
	input.context.actor_context.permissions[_] == input.action_type
}

eval_operator if {
	dev_owner
}

eval_operator if {
	input.context.actor_context.permissions[_] == "eval.adapter.run"
}

observability_writer if {
	input.context.actor_context.actor_type == "system"
}

api_support_reader if {
	dev_owner
}

api_support_reader if {
	input.context.actor_context.permissions[_] == "trace.read"
}

api_support_reader if {
	input.context.actor_context.permissions[_] == "api.request.read"
}

api_support_admin if {
	dev_owner
}

api_support_admin if {
	admin_or_owner
}

api_support_admin if {
	input.context.actor_context.permissions[_] == "api.openapi_hygiene.read"
}

evidence_action if {
	input.action_type == "evidence.read"
}

evidence_action if {
	input.action_type == "evidence.search"
}

evidence_action if {
	input.action_type == "evidence.link"
}

evidence_action if {
	input.action_type == "evidence.ground"
}

evidence_action if {
	input.action_type == "evidence.delete"
}

evidence_read_action if {
	input.action_type == "evidence.read"
}

evidence_read_action if {
	input.action_type == "evidence.search"
}

restricted_evidence_without_permission if {
	input.context.sensitivity == "restricted"
	not evidence_restricted_read
}

evidence_restricted_read if {
	input.context.permissions[_] == "evidence.restricted.read"
}

evidence_restricted_read if {
	input.context.actor_context.permissions[_] == "evidence.restricted.read"
}

identity_action if {
	input.action_type == "identity.actor.create"
}

identity_action if {
	input.action_type == "identity.actor.read"
}

identity_action if {
	input.action_type == "identity.actor.disable"
}

identity_action if {
	input.action_type == "identity.workspace.create"
}

identity_action if {
	input.action_type == "identity.workspace.read"
}

identity_action if {
	input.action_type == "identity.workspace.archive"
}

identity_action if {
	input.action_type == "identity.membership.create"
}

identity_action if {
	input.action_type == "identity.membership.read"
}

identity_action if {
	input.action_type == "identity.membership.revoke"
}

identity_action if {
	input.action_type == "identity.permission.create"
}

identity_action if {
	input.action_type == "identity.permission.read"
}

identity_action if {
	input.action_type == "identity.permission.revoke"
}

identity_read_action if {
	input.action_type == "identity.actor.read"
}

identity_read_action if {
	input.action_type == "identity.workspace.read"
}

identity_read_action if {
	input.action_type == "identity.membership.read"
}

identity_read_action if {
	input.action_type == "identity.permission.read"
}

identity_mutation_action if {
	identity_action
	not identity_read_action
}

scope_action if {
	input.action_type == "scope.resolve"
}

actor_context_present if {
	input.context.actor_context.actor_id
}

dev_owner if {
	input.context.actor_context.dev_mode == true
	input.context.actor_context.roles[_] == "owner"
}

admin_or_owner if {
	input.context.actor_context.roles[_] == "owner"
}

admin_or_owner if {
	input.context.actor_context.roles[_] == "admin"
}

permission_present if {
	input.context.permissions[_] == input.action_type
}

permission_present if {
	input.context.actor_context.permissions[_] == input.action_type
}

valid_execution_mode if {
	input.context.mode == "dry_run"
}

valid_execution_mode if {
	input.context.mode == "controlled"
}

valid_task_run_mode if {
	input.context.run_mode == "dry_run"
}

valid_task_run_mode if {
	input.context.run_mode == "controlled"
}

permissions_within_scope if {
	every permission in input.requested_permissions {
		input.security_scope[_] == permission
	}
}
