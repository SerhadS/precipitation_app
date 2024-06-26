# # Use the official PostgreSQL image as the base
FROM python:3.11

# # Set environment variables
# ENV POSTGRES_USER=username
# ENV POSTGRES_PASSWORD=password
# ENV POSTGRES_DB=aon
# ENV POSTGRES_PORT=5432
# EXPOSE 5432

# # Install Python
# RUN apt-get update && apt-get install -y \
#     python3.11 \
#     python3-pip \
#     python3.11-venv \
#     && rm -rf /var/lib/apt/lists/*

# RUN python3 -m venv aon
# # Enable venv
# ENV PATH="/aon/bin:$PATH"

COPY src /src/
COPY data /data/
RUN chmod +x /src
RUN chmod +x /data
# install requirements
RUN pip3 install --no-cache-dir -r src/requirements.txt

RUN mkdir -p /data/


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


EXPOSE 4255

ENTRYPOINT ["/entrypoint.sh"]


