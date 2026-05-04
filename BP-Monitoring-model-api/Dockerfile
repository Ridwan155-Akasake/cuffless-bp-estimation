# Step 1: Use a Python base image
FROM python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the current directory contents into the container
COPY . /app

# Step 4: Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Expose port 7860 (Hugging Face default port)
EXPOSE 7860

# Step 6: Set environment variables (optional)
ENV FLASK_ENV=production

# Step 7: Start the Flask app
CMD ["python", "app.py"]
