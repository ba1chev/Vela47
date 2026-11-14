import json
import uuid
import subprocess
from typing import Optional

from app.intelligence.agents import AgentBase
from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase
from app.intelligence.agents import A2A_DOCKER_SEND_SCRIPT
from app.intelligence.agents import A2A_DOCKER_RECEIVE_SCRIPT


class A2AInteractionDocker(A2AInteractionBase):
    """Two subagents whose sandboxes are containers on the same host, talking through
    those containers. The sandbox network keeps every container from reaching another,
    so _connect() creates a network for these two alone, internal and with an isolated
    gateway like the sandbox network, and _disconnect() removes it. Opening it never
    opens one user's container to another's.

    A text crosses it once per direction: a one-shot listener in the receiving container,
    a one-shot sender in the other with the text on its stdin. Neither outlives the
    transfer, like every other command in a sandbox."""

    PORT = 4747
    TIMEOUT_SECONDS = 30

    def __init__(self, left_container: str, right_container: str) -> None:
        if left_container == right_container:
            raise ValueError("The two agents of a Docker interaction need a container each.")
        super().__init__()
        self._left_container: str = left_container
        self._right_container: str = right_container
        self._network: str = f"vela47-a2a-{uuid.uuid4().hex[:12]}"
        self._addresses: dict[str, str] = {}

    @property
    def interaction_type(self) -> A2AInteractionType:
        return A2AInteractionType.DOCKER

    @property
    def network(self) -> str:
        return self._network

    def _container_of(self, agent: AgentBase) -> str:
        return self._left_container if agent is self._left else self._right_container

    def _docker(self, *arguments: str, input: Optional[str] = None,
        timeout: int = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["docker", *arguments],
            input = input,
            capture_output = True,
            encoding = "utf-8",
            timeout = timeout,
            check = False
        )

    def _address(self, container: str) -> str:
        inspected = self._docker("inspect", "--format", "{{json .NetworkSettings.Networks}}", container)
        networks = json.loads(inspected.stdout or "{}")
        return (networks.get(self._network) or {}).get("IPAddress", "")

    def _connect(self) -> None:
        steps = [
            (
                "network", "create", "--internal",
                "--opt", "com.docker.network.bridge.gateway_mode_ipv4=isolated", self._network
            ),
            ("network", "connect", self._network, self._left_container),
            ("network", "connect", self._network, self._right_container)
        ]
        for current_step in steps:
            completed = self._docker(*current_step)
            if completed.returncode != 0:
                self._disconnect()
                raise RuntimeError(
                    f"Could not connect {self._left_container} and {self._right_container}: "
                    f"{completed.stderr.strip()}"
                )

        self._addresses = {
            current_container: self._address(current_container)
            for current_container in (self._left_container, self._right_container)
        }
        if not all(self._addresses.values()):
            self._disconnect()
            raise RuntimeError(f"A container has no address on {self._network}.")

    def _disconnect(self) -> None:
        for current_step in (
            ("network", "disconnect", "--force", self._network, self._left_container),
            ("network", "disconnect", "--force", self._network, self._right_container),
            ("network", "rm", self._network)
        ):
            try:
                self._docker(*current_step)
            except (OSError, subprocess.TimeoutExpired):
                continue
        self._addresses = {}

    def _transfer(self, sender: AgentBase, receiver: AgentBase, text: str) -> str:
        sender_container, receiver_container = self._container_of(sender), self._container_of(receiver)
        arguments = [self._addresses[receiver_container], str(self.PORT), str(self.TIMEOUT_SECONDS)]
        listener = subprocess.Popen(
            ["docker", "exec", receiver_container, "python", "-c", A2A_DOCKER_RECEIVE_SCRIPT, *arguments],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            encoding = "utf-8"
        )
        try:
            sent = self._docker(
                "exec", "-i", sender_container, "python", "-c", A2A_DOCKER_SEND_SCRIPT, *arguments,
                input = text, timeout = self.TIMEOUT_SECONDS + 10
            )
            if sent.returncode != 0:
                listener.kill()
            received, errors = listener.communicate(timeout = self.TIMEOUT_SECONDS + 10)
        except subprocess.TimeoutExpired:
            listener.kill()
            listener.communicate()
            raise RuntimeError(
                f"The message from {sender_container} did not reach {receiver_container} "
                f"within {self.TIMEOUT_SECONDS}s."
            )

        if sent.returncode != 0 or listener.returncode != 0:
            raise RuntimeError(
                f"The message from {sender_container} could not be delivered to {receiver_container}: "
                f"{(sent.stderr if sent.returncode != 0 else errors).strip()}"
            )
        return received
