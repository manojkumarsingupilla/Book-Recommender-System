# Base image
FROM python:3.12-slim

# Expose Streamlit port
EXPOSE 8501

# Install essential build tools and git
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only necessary files to avoid large .git and LFS objects
COPY requirements.txt ./           
COPY app.py ./                     
COPY templates/ ./templates/      
COPY artifacts/ ./artifacts/       
# Add any other directories you need explicitly

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
