FROM jozo/pyqt5

RUN apt-get update && \
    apt-get install -y python3-opencv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY main.py .

CMD ["python3", "main.py"]
