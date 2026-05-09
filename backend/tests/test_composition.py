import unittest

from application.pipelines.pet_log_graph import LangGraphPetLogAgentPipeline
from composition import build_pet_log_agent_pipeline


class TestComposition(unittest.TestCase):
    def test_build_pet_log_agent_pipeline_returns_pipeline(self):
        pipeline = build_pet_log_agent_pipeline()

        self.assertIsInstance(pipeline, LangGraphPetLogAgentPipeline)
