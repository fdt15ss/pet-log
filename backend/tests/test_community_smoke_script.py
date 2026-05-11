import io
import runpy
import unittest
from contextlib import redirect_stdout


class TestCommunitySmokeScript(unittest.TestCase):
    def test_smoke_community_script_runs_api_flow(self):
        output = io.StringIO()

        with redirect_stdout(output):
            runpy.run_path("scripts/smoke_community.py", run_name="__main__")

        text = output.getvalue()
        self.assertIn("[manual smoke] community api", text)
        self.assertIn("boards: 유기동물, 용품 나눔, 자유게시판, 행동 고민, 후기", text)
        self.assertIn("[GET latest]", text)
        self.assertIn("[POST post/comment/reaction]", text)
        self.assertIn("created board: 후기", text)
        self.assertIn("updated counts: comments=1 likes=1", text)


if __name__ == "__main__":
    unittest.main()
