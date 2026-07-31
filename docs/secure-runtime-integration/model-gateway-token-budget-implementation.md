# Model Gateway Token Budget Implementation

Token budgets use the deterministic estimate `ceil(UTF-8 byte count / 3)` and label it as an estimate. AION-233 does not use provider-native tokenizers.

Input-token, requested output-token, and session-token overflows fail closed. The gateway cannot represent provider tokenizer output or chargeable provider usage.
