# run.py

import os
from dotenv import load_dotenv
from app import app

load_dotenv()  # Load variables from .env file


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


if __name__ == '__main__':
    app.run(debug=True)
