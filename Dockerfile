# Example Dockerfile
FROM python:3.9  

# Set the working directory in the container
WORKDIR /code

# Install any needed packages specified in requirements.txt
# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /code
COPY . /code

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "run.py", "provider", "service"]
