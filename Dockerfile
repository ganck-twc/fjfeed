FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY fj_moc_moo_discord.py .
CMD ["python", "fj_moc_moo_discord.py"]
