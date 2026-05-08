FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 9000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:9000", "research_paper_agent.api:create_app()"]
