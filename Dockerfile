# Use a slim version of Python for a lightweight container
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all local files into the container
COPY . .

# Install required Python dependencies and ensure the latest python-telegram-bot is installed
RUN pip install --no-cache-dir --upgrade python-telegram-bot flask reportlab

RUN <<EOT bash # Install dependencies and clean up
    apt-get update
    apt-get upgrade -y -o Dpkg::Options::="--force-confold"
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends iputils-ping vim
    apt-get clean
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

# Start both the bot and Flask web app
CMD ["sh", "-c", "python bot.py & python web_app.py"]
