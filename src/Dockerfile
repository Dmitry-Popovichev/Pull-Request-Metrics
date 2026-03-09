FROM python:3.12-slim

WORKDIR /app

COPY main.py .
COPY vars.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

CMD ["python", "main.py", "--log-level=INFO"]
