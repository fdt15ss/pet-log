import importlib
import unittest


class TestPackageStructure(unittest.TestCase):
    def test_target_architecture_packages_are_importable(self):
        modules = (
            "application.interfaces",
            "application.interfaces.agents",
            "application.interfaces.composers",
            "application.interfaces.pipelines",
            "application.interfaces.policies",
            "application.interfaces.providers",
            "application.interfaces.repositories",
            "application.agents.record_structuring",
            "application.pipelines.pet_log_agent",
            "agent_runtime.runtime",
            "agent_runtime.prompts",
            "agent_runtime.tool_registry",
            "agent_runtime.memory",
            "middleware.safety",
            "middleware.logging",
            "middleware.tracing",
            "middleware.retry",
            "middleware.validation",
            "tools.record_tools",
            "tools.profile_tools",
            "tools.schedule_tools",
            "tools.care_tools",
            "tools.speech_tools",
            "infrastructure.llm.record_structuring",
            "infrastructure.llm.record_structuring.mapper",
            "infrastructure.llm.record_structuring.model",
            "infrastructure.llm.record_structuring.prompt",
            "infrastructure.llm.record_structuring.provider",
            "infrastructure.llm.record_structuring.schema",
            "infrastructure.llm.record_summary",
            "infrastructure.llm.record_summary.mapper",
            "infrastructure.llm.record_summary.model",
            "infrastructure.llm.record_summary.prompt",
            "infrastructure.llm.record_summary.provider",
            "infrastructure.llm.record_summary.schema",
            "infrastructure.llm.image_record_understanding_provider",
            "infrastructure.speech.speech_to_text",
            "infrastructure.speech.text_to_speech",
            "infrastructure.repositories.record_repository",
            "infrastructure.policies.safety_guard",
            "infrastructure.policies.cause_hypothesis_policy",
            "infrastructure.policies.proactive_question_policy",
            "infrastructure.notifications.notification_policy",
            "infrastructure.agents.record_summary_agent",
            "infrastructure.agents.proactive_question_agent",
            "infrastructure.agents.notification_agent",
            "infrastructure.agents.photo_record_understanding_agent",
            "infrastructure.composers.home_feed_composer",
            "infrastructure.composers.record_summary_composer",
            "presentation.cli",
            "presentation.http",
            "composition",
        )

        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_interface_names_use_interface_suffix(self):
        interfaces = importlib.import_module("application.interfaces")

        self.assertTrue(hasattr(interfaces, "PetLogAgentPipelineInterface"))
        self.assertTrue(hasattr(interfaces, "RecordSummaryAgentInterface"))
        self.assertTrue(hasattr(interfaces, "RecordSummaryProviderInterface"))
        self.assertTrue(hasattr(interfaces, "ProactiveQuestionAgentInterface"))
        self.assertTrue(hasattr(interfaces, "NotificationAgentInterface"))
        self.assertTrue(hasattr(interfaces, "PhotoRecordUnderstandingAgentInterface"))
        self.assertTrue(hasattr(interfaces, "RecordStructurerInterface"))
        self.assertTrue(hasattr(interfaces, "ImageRecordUnderstandingProviderInterface"))
        self.assertTrue(hasattr(interfaces, "SpeechToTextInterface"))
        self.assertTrue(hasattr(interfaces, "TextToSpeechInterface"))
        self.assertFalse(hasattr(interfaces, "PetLogAgentPipelinePort"))
