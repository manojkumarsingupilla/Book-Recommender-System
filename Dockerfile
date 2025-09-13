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

# Copy project files first (setup.py, requirements.txt, etc.)
COPY requirements.txt setup.py README.md ./

# Copy the rest of your app
COPY app.py ./                     
COPY templates/ ./templates/      
COPY artifacts/ ./artifacts/      
COPY books_recommender/ ./books_recommender/

# Install Python dependencies (this will now work with -e .)
RUN pip install --no-cache-dir -r requirements.txt

# Run Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
