# HOW TO RUN DOCKER APPLICATION

docker build -t restapi-flask-app .

docker run -dp 5000:5000 -w /app -v ${PWD}:/app restapi-flask-app

docker-compose up --build

.\.venv\Scripts\Activate.ps1
