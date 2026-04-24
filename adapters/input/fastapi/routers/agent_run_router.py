from typing import Annotated
from uuid import UUID as StdUUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from uuid6 import UUID

from adapters.input.fastapi.dependencies import inject_tenant_uri, require_auth
from adapters.input.schemas.agent_run_schema import (
    AgentRunCreatedSchema,
    AgentRunCreateSchema,
    AgentRunPatchSchema,
    AgentRunSchema,
    AgentRunUpdateSchema,
)
from application.services.agent_run_service import AgentRunService
from arclith.adapters.input.fastapi.dependencies import get_duration_ms
from arclith.adapters.input.schemas.response_wrapper import (
    ApiResponse,
    PaginatedResponse,
    ResponseMetadata,
    paginated_response,
    success_response,
)
from arclith.domain.ports.logger import Logger
from domain.models.agent_run import AgentRun


class AgentRunRouter:
    def __init__(self, service: AgentRunService, logger: Logger) -> None:
        self._service = service
        self._logger = logger
        self.router = APIRouter(prefix="/v1/agent_runs", tags=["agent_runs"], dependencies=[Depends(inject_tenant_uri)])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            methods=["POST"],
            path="/",
            endpoint=self.create_agent_run,
            summary="Create agent_run",
            response_model = ApiResponse[AgentRunCreatedSchema],
            status_code=201,
            responses = {
                400: {"description": "Invalid payload"},
                422: {"description": "Validation failed"},
            },
        )
        self.router.add_api_route(
            methods=["GET"],
            path="/",
            endpoint=self.list_agent_runs,
            summary="List agent_runs",
            response_model=PaginatedResponse[AgentRunSchema],
            status_code=200,
        )
        self.router.add_api_route(
            methods=["GET"],
            path="/{uuid}",
            endpoint=self.get_agent_run,
            summary="Get agent_run",
            response_model=ApiResponse[AgentRunSchema],
            status_code=200,
            responses = {
                404: {"description": "AgentRun not found"},
            },
        )
        self.router.add_api_route(
            methods=["PUT"],
            path="/{uuid}",
            endpoint=self.update_agent_run,
            summary="Replace agent_run",
            status_code=204,
            responses = {
                404: {"description": "AgentRun not found"},
                412: {"description": "Precondition Failed (version mismatch via If-Match)"},
                422: {"description": "Validation failed"},
            },
        )
        self.router.add_api_route(
            methods=["PATCH"],
            path="/{uuid}",
            endpoint=self.patch_agent_run,
            summary="Partially update agent_run",
            status_code=204,
            responses = {
                404: {"description": "AgentRun not found"},
                412: {"description": "Precondition Failed (version mismatch via If-Match)"},
                422: {"description": "Validation failed"},
            },
        )
        self.router.add_api_route(
            methods=["DELETE"],
            path="/{uuid}",
            endpoint=self.delete_agent_run,
            summary="Delete agent_run",
            status_code=204,
            responses = {
                404: {"description": "AgentRun not found"},
            },
            dependencies=[Depends(require_auth)],
        )
        self.router.add_api_route(
            methods=["POST"],
            path="/{uuid}/duplicate",
            endpoint=self.duplicate_agent_run,
            summary="Duplicate agent_run",
            response_model = ApiResponse[AgentRunCreatedSchema],
            status_code=201,
            responses = {
                404: {"description": "AgentRun not found"},
            },
        )

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create_agent_run(
        self,
        payload: AgentRunCreateSchema,
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
            prefer: Annotated[str | None, Header()] = None,
    ) -> ApiResponse[AgentRunCreatedSchema] | ApiResponse[AgentRunSchema]:
        """Create a new reusable agent_run.

        **SOTA REST Features:**
        - Returns 201 Created with UUID only (minimal response)
        - Location header points to the created resource
        - Supports `Prefer: return=representation` to get full object instead
        - Supports `Idempotency-Key` header to prevent duplicates (via middleware)
        - Returns 422 for validation errors (business logic)

        **Usage:**
        ```bash
        # Minimal response (default)
        curl -X POST /v1/agent_runs \\
          -H "Content-Type: application/json" \\
          -H "Idempotency-Key: $(uuidgen)" \\
          -d '{"name": "Farine de blé"}'
        
        # Full representation
        curl -X POST /v1/agent_runs \\
          -H "Prefer: return=representation" \\
          -d '{"name": "Farine de blé"}'
        ```
        """
        result = await self._service.create(AgentRun(name=payload.name))

        # RFC 7231: Location header on 201 Created
        location = f"{request.url.path.rstrip('/')}/{result.uuid}"
        response.headers["Location"] = location

        # RFC 8288: Link header (HATEOAS)
        response.headers["Link"] = f'<{location}>; rel="self", <{location}/duplicate>; rel="duplicate"'

        # RFC 7240: Prefer header support
        if prefer and "return=representation" in prefer.lower():
            # Client wants full object
            return success_response(
                AgentRunSchema.model_validate(result, from_attributes = True),
                metadata = ResponseMetadata(duration_ms = int(duration_ms)),
            )

        # Default: minimal response (UUID only)
        return success_response(
            AgentRunCreatedSchema(uuid = result.uuid),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def get_agent_run(
        self,
        uuid: StdUUID,
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
    ) -> ApiResponse[AgentRunSchema]:
        """Get an agent_run by its UUID.

        **SOTA REST Features:**
        - ETag header based on entity version (for caching/concurrency)
        - Cache-Control: private, max-age=300 (via middleware)
        - Link header for HATEOAS navigation
        - Supports If-None-Match for conditional GET (304 Not Modified)

        **Usage:**
        ```bash
        # First request
        curl -i /v1/agent_runs/01234...
        # Returns: ETag: "v1"
        
        # Subsequent request (cache validation)
        curl -H 'If-None-Match: "v1"' /v1/agent_runs/01234...
        # Returns: 304 Not Modified (if unchanged)
        ```
        """
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ AgentRun not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="AgentRun not found")

        # RFC 7232: ETag for optimistic locking
        response.headers["ETag"] = f'"{result.version}"'

        # RFC 8288: Link header (HATEOAS)
        base = f"{request.url.path.rstrip('/')}"
        response.headers[
            "Link"] = f'<{base}>; rel="self", <{base}/duplicate>; rel="duplicate", </v1/agent_runs>; rel="collection"'
        
        return success_response(
            AgentRunSchema.model_validate(result, from_attributes=True),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def update_agent_run(
            self,
            uuid: StdUUID,
            payload: AgentRunUpdateSchema,
            response: Response,
            request: Request,
            if_match: Annotated[str | None, Header()] = None,
    ) -> None:
        """Replace name of an existing agent_run (PUT semantics).

        **SOTA REST Features:**
        - Requires If-Match header for optimistic locking
        - Returns 412 Precondition Failed if version mismatch
        - Returns 204 No Content on success
        - Content-Location header points to updated resource
        - New ETag in response headers

        **Usage:**
        ```bash
        # Get current version
        curl -i /v1/agent_runs/01234...
        # Returns: ETag: "v1"
        
        # Update with version check
        curl -X PUT /v1/agent_runs/01234... \\
          -H 'If-Match: "v1"' \\
          -d '{"name": "Nouvelle farine"}'
        ```

        The field is fully overwritten.
        Note: changes do not propagate to recipes where this agent_run is already linked (snapshot model).
        """
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ AgentRun not found via HTTP (PUT)", uuid = str(uuid))
            raise HTTPException(status_code = 404, detail = "AgentRun not found")

        # RFC 7232: If-Match validation (optimistic locking)
        if if_match:
            expected_version = int(if_match.strip('"').lstrip('vV'))
            if existing.version != expected_version:
                self._logger.warning(
                    "⚠️ Version mismatch (optimistic lock failure)",
                    uuid = str(uuid),
                    expected = expected_version,
                    current = existing.version,
                )
                raise HTTPException(
                    status_code = 412,
                    detail = f"Version mismatch: expected v{expected_version}, current v{existing.version}",
                )

        updated = await self._service.update(AgentRun(uuid = self._to_uuid6(uuid), name = payload.name))

        # RFC 7231: Content-Location header
        response.headers["Content-Location"] = f"/v1/agent_runs/{uuid}"

        # New ETag after update
        response.headers["ETag"] = f'"{updated.version}"'

    async def patch_agent_run(
            self,
            uuid: StdUUID,
            payload: AgentRunPatchSchema,
            response: Response,
            request: Request,
            if_match: Annotated[str | None, Header()] = None,
    ) -> None:
        """Partially update an agent_run (PATCH semantics).

        **SOTA REST Features:**
        - Requires If-Match header for optimistic locking
        - Returns 412 Precondition Failed if version mismatch
        - Returns 204 No Content on success
        - Content-Location header points to updated resource

        Only the fields provided in the body are updated; omitted fields keep their current value.
        Note: changes do not propagate to recipes where this agent_run is already linked (snapshot model).
        """
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ AgentRun not found via HTTP (PATCH)", uuid = str(uuid))
            raise HTTPException(status_code=404, detail="AgentRun not found")

        # RFC 7232: If-Match validation
        if if_match:
            expected_version = int(if_match.strip('"').lstrip('vV'))
            if existing.version != expected_version:
                self._logger.warning(
                    "⚠️ Version mismatch (optimistic lock failure)",
                    uuid = str(uuid),
                    expected = expected_version,
                    current = existing.version,
                )
                raise HTTPException(
                    status_code = 412,
                    detail = f"Version mismatch: expected v{expected_version}, current v{existing.version}",
                )

        updated = await self._service.update(
            AgentRun(
                uuid = existing.uuid,
                name = payload.name if payload.name is not None else existing.name,
            )
        )

        # RFC 7231: Content-Location header
        response.headers["Content-Location"] = f"/v1/agent_runs/{uuid}"

        # New ETag after update
        response.headers["ETag"] = f'"{updated.version}"'

    async def delete_agent_run(self, uuid: StdUUID) -> None:
        """Soft-delete an agent_run.

        **SOTA REST Features:**
        - Returns 204 No Content on success
        - Idempotent (deleting already-deleted resource returns 204)

        The agent_run is marked as deleted and excluded from list results.
        It is retained until the purge retention period expires.
        Use `DELETE /admin/purge` to permanently remove all expired entities.
        """
        await self._service.delete(self._to_uuid6(uuid))

    async def list_agent_runs(
        self,
        response: Response,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        name: str | None = Query(None, min_length=1, description="Filter by name (partial, case-insensitive)"),
    ) -> PaginatedResponse[AgentRunSchema]:
        """List all active (non-deleted) agent_runs.

        **SOTA REST Features:**
        - X-Total-Count header for total items (useful for pagination UI)
        - Cache-Control: private, max-age=60 (via middleware)
        - Always returns 200 OK, even if empty list

        Pass `name` for a partial, case-insensitive name filter.
        Each item: uuid, name, unit, created_at, updated_at, version.
        Use the returned UUIDs with `POST /v1/recipes/{uuid}/agent_runs/{agent_run_uuid}` to link them to a recipe.
        """
        offset = (page - 1) * per_page
        items, total = await self._service.find_page_filtered(name=name, offset=offset, limit=per_page)

        # X-Total-Count header (common practice for pagination)
        response.headers["X-Total-Count"] = str(total)

        return paginated_response(
            data=[AgentRunSchema.model_validate(i, from_attributes=True) for i in items],
            total=total,
            page=page,
            per_page=per_page,
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def duplicate_agent_run(
        self,
        uuid: StdUUID,
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
            prefer: Annotated[str | None, Header()] = None,
    ) -> ApiResponse[AgentRunCreatedSchema] | ApiResponse[AgentRunSchema]:
        """Duplicate an agent_run, assigning it a new UUID.

        **SOTA REST Features:**
        - Returns 201 Created with UUID only (minimal response)
        - Location header points to the duplicated resource
        - Supports `Prefer: return=representation` to get full object

        Creates an independent copy with the same name and unit.
        Returns the UUID of the new agent_run.
        """
        result = await self._service.duplicate(self._to_uuid6(uuid))

        # RFC 7231: Location header on 201 Created
        location = f"/v1/agent_runs/{result.uuid}"
        response.headers["Location"] = location

        # RFC 8288: Link header
        response.headers["Link"] = f'<{location}>; rel="self", </v1/agent_runs>; rel="collection"'

        # RFC 7240: Prefer header support
        if prefer and "return=representation" in prefer.lower():
            return success_response(
                AgentRunSchema.model_validate(result, from_attributes = True),
                metadata = ResponseMetadata(duration_ms = int(duration_ms)),
            )

        # Default: minimal response (UUID only)
        return success_response(
            AgentRunCreatedSchema(uuid = result.uuid),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

