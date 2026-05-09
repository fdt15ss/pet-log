from pathlib import Path

from dotenv import load_dotenv

from presentation.http import create_app


load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

app = create_app()
