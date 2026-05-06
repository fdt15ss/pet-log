from __future__ import annotations

from application.interfaces import PetLogAgentPipelineInterface
from application.agents.context_analysis import ContextAnalysisAgent
from application.agents.record_structuring import RecordStructuringAgent
from application.agents.reminder import ReminderAgent
from application.agents.risk_detection import RiskDetectionAgent
from application.agents.suggestion import SuggestionAgent
from application.pipelines.pet_log_agent import PetLogAgentPipeline
from infrastructure.llm.record_structurer import RecordStructurer
from infrastructure.policies.missing_record_policy import MissingRecordPolicy
from infrastructure.policies.pattern_analyzer import PatternAnalyzer
from infrastructure.policies.reminder_planner import ReminderPlanner
from infrastructure.policies.risk_signal_policy import RiskSignalPolicy
from infrastructure.policies.suggestion_composer import SuggestionComposer
from infrastructure.repositories.record_repository import RecordRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository


def build_pet_log_agent_pipeline() -> PetLogAgentPipelineInterface:
    record_repository = RecordRepository()
    schedule_repository = ScheduleRepository()
    return PetLogAgentPipeline(
        record_structuring_agent=RecordStructuringAgent(RecordStructurer()),
        record_history_reader=record_repository,
        schedule_context_reader=schedule_repository,
        context_analysis_agent=ContextAnalysisAgent(PatternAnalyzer(), MissingRecordPolicy()),
        risk_detection_agent=RiskDetectionAgent(RiskSignalPolicy()),
        record_repository=record_repository,
        suggestion_agent=SuggestionAgent(SuggestionComposer()),
        reminder_agent=ReminderAgent(ReminderPlanner()),
    )
