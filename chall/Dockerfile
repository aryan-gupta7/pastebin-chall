FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libatk1.0-0 libgtk-3-0 \
    chromium chromium-driver \
  && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/chromium /usr/bin/google-chrome \
  && ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000
CMD ["python", "app.py"]

