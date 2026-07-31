# Model Gateway Boundary

AION-233 may implement the recorded future source scope only after `AION-232-SRI-0002`. AION-232 creates no model-gateway runtime source and changes no Brain runtime source.

Allowed future operations are `model_gateway.health.read, model_gateway.observability.read, model_gateway.route.plan, model_gateway.text.generate.simulate, model_gateway.structured.generate.simulate`. All provider calls, provider network egress, provider SDK use, credentials, tokens, connector execution, tool execution, memory writes, policy mutation, belief mutation, source rewrite, deployment, model training, v0.2 tags, and v0.2 releases remain disabled.
