FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt ./apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

COPY apps/api/ /app/apps/api/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app

CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
