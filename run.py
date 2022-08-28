import os
from pathlib import Path
from dotenv import load_dotenv
from app import flask_app

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

if __name__ == '__main__':
    flask_app.run(port=int(os.environ.get("PORT", 5000)))
