import uvicorn

from config.settings import settings
from utils.logging import setup_logging

if __name__ == "__main__":
    setup_logging()
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=False)
