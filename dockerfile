# Base image with more packages pre-installed
FROM python:3.11

# Setup working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install only essential packages
RUN apt-get update && apt-get install -y \
    default-jdk \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Setup JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="$JAVA_HOME/bin:$PATH"

# Set the time zone
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["bash"]