FROM python:3.11-slim

WORKDIR /app
COPY log_poem.py .

RUN pip install requests

CMD ["python", "log_poem.py"]
