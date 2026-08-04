from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.config import AppConfig  # noqa: E402

app = create_app()


if __name__ == "__main__":
    app.run(host=AppConfig.APP_HOST, port=AppConfig.APP_PORT)
