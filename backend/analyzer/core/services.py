from .clustering import TopicClusteredService
from .summary import SummaryService

_topic_service: TopicClusteredService | None = None
_summary_service: SummaryService | None = None


def get_topic_service() -> TopicClusteredService:
    global _topic_service
    if _topic_service is None:
        _topic_service = TopicClusteredService()
    return _topic_service


def get_summary_service() -> SummaryService | None:
    global _summary_service
    if _summary_service is not None:
        return _summary_service
    try:
        _summary_service = SummaryService()
    except Exception as e:
        print(f"SummaryService disabled: {e}")
        _summary_service = None
    return _summary_service
