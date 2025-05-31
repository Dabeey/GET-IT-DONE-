FROM python:3.13.2

WORKDIR /app

COPY requirements.txt .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["python", "app.py"]
# This Dockerfile sets up a Python environment, installs dependencies from requirements.txt,