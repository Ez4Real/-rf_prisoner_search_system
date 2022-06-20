from pathlib import Path
from fastapi.staticfiles import StaticFiles

from prisoners.__init__ import create_app

BASE_DIR = Path(__file__).resolve().parent

app = create_app()

app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')