FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
ENV DATABASE_URL=postgresql://trekdb_owner:npg_rcIU0Y8VuZMC@ep-dry-bonus-a5r1yrig-pooler.us-east-2.aws.neon.tech/trekdb?sslmode=require

COPY . .

EXPOSE 8080 

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "server:app"]