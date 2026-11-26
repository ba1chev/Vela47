from enum import Enum


class InfrastructureChange(str, Enum):
    """Enumerates what a release does to the infrastructure of an environment. ADDITIVE
    adds resources or capacity that the running release does not notice, so it may ship
    together with the code that uses it, since the deployment applies Terraform first.
    BREAKING removes, shrinks or replaces something the running release may use, so it
    ships alone, after the code no longer depends on it (see docs/change_management.md)."""

    NONE = "none"
    ADDITIVE = "additive"
    BREAKING = "breaking"
