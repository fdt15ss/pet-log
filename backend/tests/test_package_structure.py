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
            "infrastructure.llm.record_structurer",
            "infrastructure.speech.speech_to_text",
            "infrastructure.speech.text_to_speech",
            "infrastructure.repositories.record_repository",
            "infrastructure.policies.safety_guard",
            "infrastructure.composers.home_feed_composer",
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
        self.assertTrue(hasattr(interfaces, "RecordStructurerInterface"))
        self.assertTrue(hasattr(interfaces, "SpeechToTextInterface"))
        self.assertTrue(hasattr(interfaces, "TextToSpeechInterface"))
        self.assertFalse(hasattr(interfaces, "PetLogAgentPipelinePort"))
