from dotenv import load_dotenv

from app import create_app
from app.config import AppConfig

load_dotenv()
app = create_app()


if __name__ == "__main__":
    app.run(host=AppConfig.APP_HOST, port=AppConfig.APP_PORT)

