# Stage 8: container for the API. Ollama runs outside (on the host or as its own container).
FROM python:3.11-slim
WORKDIR /srv
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt
COPY src/ src/
COPY app/ app/
COPY configs/ configs/
COPY policies/ policies/
# data/shop.db and results/intent_model.joblib are mounted at run time, not baked into the image
ENV SUPPORT_ROOT=/srv OLLAMA_HOST=http://host.docker.internal:11434
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
