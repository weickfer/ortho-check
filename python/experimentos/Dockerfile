FROM python:3.11-slim

WORKDIR /experimentos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "comparar_avanco.py"]
