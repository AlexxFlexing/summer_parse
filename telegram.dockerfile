FROM python:3.11-slim

RUN mkdir -p /app/csv, /app/png

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY settings.py /app/settings.py

COPY analysis.py /app/analysis.py

COPY bot.py /app/bot.py

COPY converter.py /app/converter.py

COPY habr.py /app/habr.py

COPY hh.py /app/hh.py

COPY views.py /app/views.py

WORKDIR /app

EXPOSE 8000

CMD ["python", "bot.py"]