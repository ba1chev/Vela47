from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationType
from app.intelligence.memory import ContextWindowOperationSlide
from app.intelligence.memory import ContextWindowOperationExpand
from app.intelligence.memory import ContextWindowOperationShrink
from app.intelligence.memory import ContextWindowOperationFlatten
from app.intelligence.memory import ContextWindowOperationTruncate
from app.intelligence.memory import ContextWindowOperationSummarize


CONTEXT_WINDOW_OPERATION_REGISTRY: dict[ContextWindowOperationType, type[ContextWindowOperation]] = {
    ContextWindowOperationType.EXPAND: ContextWindowOperationExpand,
    ContextWindowOperationType.SHRINK: ContextWindowOperationShrink,
    ContextWindowOperationType.SLIDE: ContextWindowOperationSlide,
    ContextWindowOperationType.SUMMARIZE: ContextWindowOperationSummarize,
    ContextWindowOperationType.TRUNCATE: ContextWindowOperationTruncate,
    ContextWindowOperationType.FLATTEN: ContextWindowOperationFlatten
}