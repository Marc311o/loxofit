FROM python:3.11-slim
LABEL authors="Jerzy Andrusiewicz"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG REQUIREMENTS=requirements.txt
COPY requirements*.txt .
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
