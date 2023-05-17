import os

# Set the working directory to the project's root directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    app.run()