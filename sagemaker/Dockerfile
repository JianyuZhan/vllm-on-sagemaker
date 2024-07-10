FROM vllm/vllm-openai:latest AS vllm-base

# Create a new stage based on vllm-base
FROM vllm-base AS sagemaker-serving

# Copy the new entrypoint script
COPY src/sagemaker_serving.py /app/sagemaker_serving.py
COPY sagemaker/serve /usr/bin/serve

# Set the working directory
WORKDIR /app

# Ensure the serve script has executable permissions
RUN chmod +x /usr/bin/serve

# Expose port 8080
EXPOSE 8080

# Set the serve script as the entrypoint
ENTRYPOINT ["/usr/bin/serve"]
