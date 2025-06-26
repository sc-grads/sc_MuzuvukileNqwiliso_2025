FROM python:3.11-slim

EXPOSE 5000

WORKDIR /app

COPY . .

RUN pip install flask

CMD ["flask", "run", "--host", "0.0.0.0"]
