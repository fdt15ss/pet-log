from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from application.agents.context_analysis import ContextAnalysisAgent
from application.agents.hospital import HospitalRecommendationAgent
from application.agents.record_structuring import RecordStructuringAgent
from application.agents.reminder import ReminderAgent
from application.agents.risk_detection import RiskDetectionAgent
from application.agents.shopping import ShoppingAgent
from application.agents.suggestion import SuggestionAgent
from application.pipelines.pet_log_graph import LangGraphPetLogAgentPipeline
from infrastructure.database import connect
from infrastructure.llm.preload import preload_configured_llm_providers
from infrastructure.llm.record_structuring import RecordStructurer
from infrastructure.maps import GooglePlacesClient
from infrastructure.policies.missing_record_policy import MissingRecordPolicy
from infrastructure.policies.pattern_analyzer import PatternAnalyzer
from infrastructure.policies.reminder_planner import ReminderPlanner
from infrastructure.policies.risk_signal_policy import RiskSignalPolicy
from infrastructure.policies.suggestion_composer import SuggestionComposer
from infrastructure.repositories.file_repository import FileRepository, LocalFileStorage
from infrastructure.repositories.community_repository import CommunityRepository
from infrastructure.repositories.pet_profile_repository import PetProfileRepository
from infrastructure.repositories.record_repository import RecordRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository
from infrastructure.shopping import NaverShoppingClient, ShoppingRecommendationProvider
from infrastructure.speech import SpeechToTextProvider
from middleware import HospitalFallbackMiddleware, ShoppingFallbackMiddleware


@dataclass(frozen=True)
class AppContext:
    pet_log_agent_pipeline: LangGraphPetLogAgentPipeline
    pet_profile_reader: PetProfileRepository
    speech_to_text: SpeechToTextProvider
    hospital_recommendation_agent: HospitalRecommendationAgent | None = None
    record_reader: RecordRepository | None = None
    schedule_reader: ScheduleRepository | None = None
    file_repository: FileRepository | None = None
    file_storage: LocalFileStorage | None = None
    community_repository: CommunityRepository | None = None
    close: Callable[[], None] = field(default=lambda: None)


def build_app_context(database_path: str | None = None) -> AppContext:
    preload_configured_llm_providers()
    database = connect(database_path)
    record_repository = RecordRepository(connection=database)
    schedule_repository = ScheduleRepository(connection=database)
    pet_profile_reader = PetProfileRepository(connection=database)
    file_repository = FileRepository(connection=database)
    community_repository = CommunityRepository(connection=database)
    pipeline = LangGraphPetLogAgentPipeline(
        record_structuring_agent=RecordStructuringAgent(RecordStructurer()),
        record_history_reader=record_repository,
        schedule_context_reader=schedule_repository,
        context_analysis_agent=ContextAnalysisAgent(PatternAnalyzer(), MissingRecordPolicy()),
        risk_detection_agent=RiskDetectionAgent(RiskSignalPolicy()),
        record_repository=record_repository,
        suggestion_agent=SuggestionAgent(SuggestionComposer()),
        reminder_agent=ReminderAgent(ReminderPlanner()),
        shopping_agent=ShoppingAgent(
            ShoppingFallbackMiddleware(ShoppingRecommendationProvider(NaverShoppingClient()))
        ),
    )
    return AppContext(
        pet_log_agent_pipeline=pipeline,
        pet_profile_reader=pet_profile_reader,
        speech_to_text=SpeechToTextProvider(),
        hospital_recommendation_agent=HospitalRecommendationAgent(HospitalFallbackMiddleware(GooglePlacesClient())),
        record_reader=record_repository,
        schedule_reader=schedule_repository,
        file_repository=file_repository,
        file_storage=LocalFileStorage(),
        community_repository=community_repository,
        close=database.close,
    )


def build_pet_log_agent_pipeline(database_path: str | None = None) -> LangGraphPetLogAgentPipeline:
    preload_configured_llm_providers()
    database = connect(database_path)
    record_repository = RecordRepository(connection=database)
    schedule_repository = ScheduleRepository(connection=database)
    return LangGraphPetLogAgentPipeline(
        record_structuring_agent=RecordStructuringAgent(RecordStructurer()),
        record_history_reader=record_repository,
        schedule_context_reader=schedule_repository,
        context_analysis_agent=ContextAnalysisAgent(PatternAnalyzer(), MissingRecordPolicy()),
        risk_detection_agent=RiskDetectionAgent(RiskSignalPolicy()),
        record_repository=record_repository,
        suggestion_agent=SuggestionAgent(SuggestionComposer()),
        reminder_agent=ReminderAgent(ReminderPlanner()),
        shopping_agent=ShoppingAgent(
            ShoppingFallbackMiddleware(ShoppingRecommendationProvider(NaverShoppingClient()))
        ),
    )


def build_pet_profile_reader(database_path: str | None = None) -> PetProfileRepository:
    database = connect(database_path)
    return PetProfileRepository(connection=database)
