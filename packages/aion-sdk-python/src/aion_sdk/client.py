"""HTTP client for AION Brain public APIs."""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any, Self, cast

import httpx

from aion_sdk.config import AIONClientConfig
from aion_sdk.errors import AIONAPIError, AIONHTTPError
from aion_sdk.headers import build_aion_headers
from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.resources.config import ConfigResource


class AIONClient:
    """Synchronous AION Brain API client."""

    def __init__(
        self,
        config: AIONClientConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config or AIONClientConfig.from_env()
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=self._config.timeout_seconds)
        self.health = _import_resource("health").HealthResource(self)
        self.kernel = _import_resource("kernel").KernelResource(self)
        self.events = _import_resource("events").EventsResource(self)
        self.memory = _import_resource("memory").MemoryResource(self)
        self.reasoning = _import_resource("reasoning").ReasoningResource(self)
        self.commands = _import_resource("commands").CommandsResource(self)
        self.workflows = _import_resource("workflows").WorkflowsResource(self)
        self.autonomy = _import_resource("autonomy").AutonomyResource(self)
        self.approvals = _import_resource("approvals").ApprovalsResource(self)
        self.visual = _import_resource("visual").VisualResource(self)
        self.modules = _import_resource("modules").ModulesResource(self)
        self.sandbox = _import_resource("sandbox").SandboxResource(self)
        self.policy = _import_resource("policy").PolicyResource(self)
        self.scenarios = _import_resource("scenarios").ScenariosResource(self)
        self.versioning = _import_resource("versioning").VersioningResource(self)
        self.release = _import_resource("release").ReleaseResource(self)
        self.backups = _import_resource("backups").BackupsResource(self)
        self.performance = _import_resource("performance").PerformanceResource(self)
        self.security = _import_resource("security").SecurityResource(self)
        self.resilience = _import_resource("resilience").ResilienceResource(self)
        self.audit = _import_resource("audit").AuditResource(self)
        self.operator = _import_resource("operator").OperatorResource(self)
        self.operator_actions = _import_resource("operator_actions").OperatorActionsResource(self)
        self.operator_console = _import_resource(
            "operator_console"
        ).OperatorConsoleResource(self)
        self.local_auth = _import_resource("local_auth").LocalAuthResource(self)
        self.local_session = _import_resource("local_session").LocalSessionResource(self)
        self.dialogue = _import_resource("dialogue").DialogueResource(self)
        self.responses = _import_resource("responses").ResponsesResource(self)
        self.beliefs = _import_resource("beliefs").BeliefsResource(self)
        self.concepts = _import_resource("concepts").ConceptsResource(self)
        self.entities = _import_resource("entities").EntitiesResource(self)
        self.situations = _import_resource("situations").SituationsResource(self)
        self.decisions = _import_resource("decisions").DecisionsResource(self)
        self.outcomes = _import_resource("outcomes").OutcomesResource(self)
        self.learning = _import_resource("learning").LearningResource(self)
        self.self_model = _import_resource("self_model").SelfModelResource(self)
        self.explanations = _import_resource("explanations").ExplanationsResource(self)
        self.instructions = _import_resource("instructions").InstructionsResource(self)
        self.grounding = _import_resource("grounding").GroundingResource(self)
        self.prompts = _import_resource("prompts").PromptsResource(self)
        self.model_outputs = _import_resource("model_outputs").ModelOutputsResource(self)
        self.model_provider_hardening = _import_resource(
            "model_provider_hardening"
        ).ModelProviderHardeningResource(self)
        self.action_proposals = _import_resource("action_proposals").ActionProposalsResource(self)
        self.run_supervision = _import_resource("run_supervision").RunSupervisionResource(self)
        self.notifications = _import_resource("notifications").NotificationsResource(self)
        self.scheduler = _import_resource("scheduler").SchedulerResource(self)
        self.incidents = _import_resource("incidents").IncidentsResource(self)
        self.registry = _import_resource("registry").RegistryResource(self)
        self.contracts = _import_resource("contracts").ContractsResource(self)
        self.lifecycle = _import_resource("lifecycle").LifecycleResource(self)
        self.extensions = _import_resource("extensions").ExtensionsResource(self)
        self.module_bindings = _import_resource("module_bindings").ModuleBindingsResource(self)
        self.module_activation = _import_resource(
            "module_activation"
        ).ModuleActivationResource(self)
        self.module_mock_runtime = _import_resource(
            "module_mock_runtime"
        ).ModuleMockRuntimeResource(self)
        self.conformance = _import_resource("conformance").ConformanceResource(self)
        self.golden_path = _import_resource("golden_path").GoldenPathResource(self)
        self.bootstrap = _import_resource("bootstrap").BootstrapResource(self)
        self.release_candidate = _import_resource("release_candidate").ReleaseCandidateResource(
            self
        )
        self.runtime_config = cast(
            "ConfigResource",
            _import_resource("config").ConfigResource(self),
        )
        self.config = _RuntimeConfigAccessor(self._config, self.runtime_config)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get(
        self,
        path: str,
        *,
        params: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONValue:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: JSONValue = None,
        params: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONValue:
        return self.request("POST", path, json=json, params=params, headers=headers)

    def delete(
        self,
        path: str,
        *,
        json: JSONValue = None,
        params: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONValue:
        return self.request("DELETE", path, json=json, params=params, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: JSONValue = None,
        params: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONValue:
        url = self._url(path)
        request_headers = build_aion_headers(self._config, headers)
        try:
            response = self._client.request(
                method,
                url,
                json=json,
                params=params,
                headers=request_headers,
                timeout=self._config.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise AIONHTTPError(str(exc)) from exc
        return _decode_response(response)

    def _url(self, path: str) -> str:
        clean = path if path.startswith("/") else f"/{path}"
        return f"{self._config.base_url}{clean}"


class AIONAsyncClient:
    """Async AION Brain API client."""

    def __init__(
        self,
        config: AIONClientConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or AIONClientConfig.from_env()
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=self.config.timeout_seconds)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: JSONValue = None,
        params: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONValue:
        clean = path if path.startswith("/") else f"/{path}"
        request_headers = build_aion_headers(self.config, headers)
        try:
            response = await self._client.request(
                method,
                f"{self.config.base_url}{clean}",
                json=json,
                params=params,
                headers=request_headers,
                timeout=self.config.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise AIONHTTPError(str(exc)) from exc
        return _decode_response(response)


def _decode_response(response: httpx.Response) -> JSONValue:
    if response.status_code == 204:
        return None
    try:
        payload = cast(JSONValue, response.json())
    except ValueError as exc:
        if response.is_error:
            raise AIONHTTPError(
                f"AION API returned HTTP {response.status_code} with non-JSON body",
                status_code=response.status_code,
            ) from exc
        return None
    if response.is_error:
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            raise AIONAPIError.from_payload(payload, status_code=response.status_code)
        raise AIONHTTPError(
            f"AION API returned HTTP {response.status_code}",
            status_code=response.status_code,
        )
    return payload


def _import_resource(name: str) -> Any:
    module = __import__(f"aion_sdk.resources.{name}", fromlist=["*"])
    return module


class _RuntimeConfigAccessor:
    """Expose runtime config APIs while preserving client config attribute reads."""

    def __init__(self, client_config: AIONClientConfig, runtime_config: ConfigResource) -> None:
        self._client_config = client_config
        self._runtime_config = runtime_config

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client_config, name)

    def __eq__(self, other: object) -> bool:
        return self._client_config == other

    @property
    def client_config(self) -> AIONClientConfig:
        return self._client_config

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._runtime_config.create_profile(payload)

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
    ) -> JSONValue:
        return self._runtime_config.list_profiles(status=status, profile_type=profile_type)

    def activate_profile(self, config_profile_id: str, reason: str) -> JSONValue:
        return self._runtime_config.activate_profile(config_profile_id, reason)

    def create_feature_override(self, payload: JSONDict) -> JSONValue:
        return self._runtime_config.create_feature_override(payload)

    def list_feature_overrides(
        self,
        *,
        feature_key: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        return self._runtime_config.list_feature_overrides(
            feature_key=feature_key,
            status=status,
        )

    def create_snapshot(self, payload: JSONDict) -> JSONValue:
        return self._runtime_config.create_snapshot(payload)

    def get_snapshot(self, config_snapshot_id: str, scope: list[str]) -> JSONValue:
        return self._runtime_config.get_snapshot(config_snapshot_id, scope)

    def compare_snapshots(self, snapshot_id_a: str, snapshot_id_b: str) -> JSONValue:
        return self._runtime_config.compare_snapshots(snapshot_id_a, snapshot_id_b)

    def validate(self, payload: JSONDict) -> JSONValue:
        return self._runtime_config.validate(payload)

    def status(self, scope: list[str]) -> JSONValue:
        return self._runtime_config.status(scope)
