"""Facade for AION Prompt Packet Compiler services."""

from __future__ import annotations

from aion_brain.contracts.prompts import PromptCompileRequest, PromptCompileResult
from aion_brain.contracts.scopes import ActorContext


class PromptGovernanceService:
    """Small facade around prompt compilation for dependent Brain modules."""

    def __init__(self, compiler: object, actor_context: ActorContext | None = None) -> None:
        self._compiler = compiler
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PromptGovernanceService:
        compile_context = getattr(self._compiler, "with_actor_context", None)
        compiler = compile_context(actor_context) if callable(compile_context) else self._compiler
        return PromptGovernanceService(compiler, actor_context)

    def compile(self, request: PromptCompileRequest) -> PromptCompileResult:
        """Compile a governed prompt packet."""

        compile_call = getattr(self._compiler, "compile", None)
        if not callable(compile_call):
            raise TypeError("prompt compiler is not callable")
        result = compile_call(request)
        if not isinstance(result, PromptCompileResult):
            raise TypeError("prompt compiler returned an invalid result")
        return result


__all__ = ["PromptGovernanceService"]
