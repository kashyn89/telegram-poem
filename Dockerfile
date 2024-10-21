FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade python-telegram-bot flask reportlab

RUN <<EOT bash # Install dependencies and clean up
    apt-get update
    apt-get upgrade -y -o Dpkg::Options::="--force-confold"
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends iputils-ping vim
    apt-get clean
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

CMD ["sh", "-c", "python bot.py & python web_app.py"]
