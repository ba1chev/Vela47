from typing import Optional

from app.intelligence.sandbox import SandboxSlot
from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationTask
from app.intelligence.messages import MessageHuman
from app.intelligence.tracing import TraceEventType
from app.intelligence.sandbox import SandboxPoolBase
from app.intelligence.agents import OperationContext
from app.intelligence.tools import ToolMessageWorker
from app.intelligence.agents import OperationSubagent
from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import A2AInteractionBase
from app.intelligence.agents import OperationLayerBase
from app.intelligence.tracing import TracingServiceNull
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.agents import A2AInteractionFactory
from app.intelligence.agents import OperationSubagentType
from app.intelligence.agents import SUBAGENT_TASK_TEMPLATE
from app.intelligence.agents import OperationSubagentResult
from app.intelligence.agents import OperationSubagentPeering
from app.intelligence.agents import A2AInteractionFactoryBase
from app.intelligence.agents import OperationSubagentFactoryBase
from app.intelligence.agents import SUBAGENT_PEER_MESSAGE_TEMPLATE


class OperationSubagentsLayer(OperationLayerBase):
    """Runs one freshly built subagent per task in a leased sandbox slot and collects
    what each produced: the report, and beside it the evidence its probes gathered. A
    failing subagent becomes an error result instead of raising, and every slot is
    released in a finally block. Each subagent sees its instruction and the user's goal
    through SUBAGENT_TASK_TEMPLATE, never the plan or the other tasks.

    With a peering, the last subagent of each type that can be messaged stays alive
    with its slot until the layer ends, and a later subagent of a messaging type gets a
    message_worker tool reaching it through an A2A interaction, connected on the first
    message and closed when the step ends. A run then holds two slots at once; when the
    pool has none left, the kept subagents are let go and the step runs without a peer."""

    def __init__(self, subagent_factory: OperationSubagentFactoryBase,
        sandbox_pool: SandboxPoolBase,
        tracing_service: Optional[TracingServiceBase] = None,
        peering: Optional[OperationSubagentPeering] = None,
        interaction_factory: Optional[A2AInteractionFactoryBase] = None) -> None:
        self._subagent_factory: OperationSubagentFactoryBase = subagent_factory
        self._sandbox_pool: SandboxPoolBase = sandbox_pool
        self._tracing_service: TracingServiceBase = (
            tracing_service
            if tracing_service is not None
            else TracingServiceNull()
        )
        self._peering: Optional[OperationSubagentPeering] = peering
        self._interaction_factory: A2AInteractionFactoryBase = (
            interaction_factory
            if interaction_factory is not None
            else A2AInteractionFactory()
        )

    @property
    def operation_type(self) -> OperationType:
        return OperationType.SUBAGENTS

    def _message(self, task: OperationTask) -> MessageHuman:
        if not task.goal:
            return MessageHuman(content = task.instruction)
        return MessageHuman(content = SUBAGENT_TASK_TEMPLATE.format(instruction = task.instruction, goal = task.goal))

    def _release(self, slot: SandboxSlot) -> None:
        self._sandbox_pool.release(slot)
        self._tracing_service.emit(
            TraceEventType.SANDBOX_RELEASED,
            f"slot {slot.id}",
            {"slot": slot.id, "available": self._sandbox_pool.available}
        )

    def _acquire(self, authors: dict[OperationSubagentType, tuple[OperationSubagent, SandboxSlot]]) -> SandboxSlot:
        try:
            return self._sandbox_pool.acquire()
        except RuntimeError:
            if not authors:
                raise
        for _, current_slot in authors.values():
            self._release(current_slot)
        authors.clear()
        return self._sandbox_pool.acquire()

    def _interaction(self, author_slot: SandboxSlot, slot: SandboxSlot) -> A2AInteractionBase:
        if self._peering.interaction_type is A2AInteractionType.DOCKER:
            return self._interaction_factory.create(
                A2AInteractionType.DOCKER,
                left_container = author_slot.reference,
                right_container = slot.reference
            )
        return self._interaction_factory.create(self._peering.interaction_type)

    def _exchange(self, interaction: A2AInteractionBase, sender: OperationSubagentType,
        receiver: OperationSubagentType, message: str) -> str:
        with self._tracing_service.span(
            TraceEventType.A2A_STARTED,
            TraceEventType.A2A_FINISHED,
            f"{sender.name} → {receiver.name}",
            {"interaction": interaction.interaction_type.value, "message": message}
        ) as span:
            try:
                interaction.establish_connection()
                content = SUBAGENT_PEER_MESSAGE_TEMPLATE.format(sender = sender.name, message = message)
                reply = interaction.send(interaction.right, MessageHuman(content = content))
            except Exception as e:
                span["status"] = "error"
                span["result"] = str(e)
                raise
            span["status"] = "success"
            span["result"] = reply.content
        return reply.content

    def _peer_of(self, task: OperationTask, slot: SandboxSlot,
        authors: dict[OperationSubagentType, tuple[OperationSubagent, SandboxSlot]]
    ) -> tuple[Optional[A2AInteractionBase], Optional[ToolMessageWorker]]:
        if self._peering is None or task.subagent_type not in self._peering.peers:
            return None, None
        peer_type = self._peering.peers[task.subagent_type]
        if peer_type not in authors:
            return None, None

        author, author_slot = authors[peer_type]
        interaction = self._interaction(author_slot, slot)
        interaction.append_left(author)
        peer_tool = ToolMessageWorker(
            send = lambda message: self._exchange(interaction, task.subagent_type, peer_type, message),
            peer_name = peer_type.name,
            max_messages = self._peering.max_messages
        )
        return interaction, peer_tool

    def _exchanges(self, peer_tool: Optional[ToolMessageWorker]) -> list[str]:
        if peer_tool is None or peer_tool.delivered == 0:
            return []
        return [
            f"The system carried {peer_tool.delivered} message(s) from this step to the "
            f"{peer_tool.peer_name} worker and its answer(s) back."
        ]

    def _keep(self, task: OperationTask, subagent: OperationSubagent, slot: SandboxSlot,
        authors: dict[OperationSubagentType, tuple[OperationSubagent, SandboxSlot]]) -> bool:
        if self._peering is None or task.subagent_type not in self._peering.peers.values():
            return False
        if task.subagent_type in authors:
            self._release(authors[task.subagent_type][1])
        authors[task.subagent_type] = (subagent, slot)
        return True

    def _run_task(self, task: OperationTask, run_id: str,
        authors: dict[OperationSubagentType, tuple[OperationSubagent, SandboxSlot]]) -> OperationSubagentResult:
        slot = self._acquire(authors)
        self._tracing_service.emit(
            TraceEventType.SANDBOX_ACQUIRED,
            f"slot {slot.id}",
            {"slot": slot.id, "available": self._sandbox_pool.available, "task_id": task.id}
        )
        kept = False
        try:
            with self._tracing_service.span(
                TraceEventType.SUBAGENT_STARTED,
                TraceEventType.SUBAGENT_FINISHED,
                task.subagent_type.name,
                {"task_id": task.id, "slot": slot.id, "instruction": task.instruction}
            ) as span:
                interaction: Optional[A2AInteractionBase] = None
                try:
                    sandbox_env = self._sandbox_pool.env_for(slot, run_id)
                    interaction, peer_tool = self._peer_of(task, slot, authors)
                    subagent = self._subagent_factory.create(task.subagent_type, sandbox_env, peer_tool = peer_tool)
                    if interaction is not None:
                        interaction.append_right(subagent)
                    response = subagent.execute(self._message(task))
                    evidence = subagent.evidence + self._exchanges(peer_tool)
                    content = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )
                    status = "success"
                except Exception as e:
                    content = str(e)
                    evidence = []
                    status = "error"
                finally:
                    if interaction is not None:
                        interaction.close_connection()
                span["status"] = status
                span["result"] = content
                span["evidence"] = evidence
            kept = status == "success" and self._keep(task, subagent, slot, authors)
            return OperationSubagentResult(
                task_id = task.id,
                subagent_type = task.subagent_type,
                content = content,
                evidence = evidence,
                status = status
            )
        finally:
            if not kept:
                self._release(slot)

    def execute(self, context: OperationContext) -> None:
        authors: dict[OperationSubagentType, tuple[OperationSubagent, SandboxSlot]] = {}
        try:
            context.results = [
                self._run_task(current_task, context.run_id, authors) for current_task in context.tasks
            ]
        finally:
            for _, current_slot in authors.values():
                self._release(current_slot)
