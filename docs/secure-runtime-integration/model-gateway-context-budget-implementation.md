# Model Gateway Context Budget Implementation

Context-budget enforcement covers message count, context item count, prompt bytes, context bytes, response bytes, structured schema bytes, and structured schema depth. Any one-over-limit value fails closed.

No routing preference, approval, cost estimate, operator request, or model choice can override a context budget failure.
