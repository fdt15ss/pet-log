from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

print("OPENAI_API_KEY in backend app:", bool(os.getenv("OPENAI_API_KEY")))

from presentation.http import create_app


app = create_app()