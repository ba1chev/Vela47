from pydantic import BaseModel, Field


class SandboxSlot(BaseModel):
    """A lease on one isolated execution environment, handed out by a
    SandboxPoolBase for the duration of a single subagent run. The slot is a
    handle, not the environment itself — it identifies which of the pool's
    pre-provisioned units the holder may use. A Docker-backed pool carries the
    container name here; the in-memory pool carries only the index."""

    id: int = Field(
        ge = 0,
        description = "Index of this slot within its pool. Stable for the pool's lifetime, so "
            "it can be logged to trace which environment ran which task."
    )
    reference: str = Field(
        default = "",
        description = "Backend-specific handle for the underlying environment — a container name "
            "for a Docker pool, empty for the in-memory pool. Callers that need to execute "
            "inside the environment resolve it through this value."
    )
