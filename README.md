# ETL Data Pipeline with Airflow, PostgreSQL, and Docker

## Overview

This project is focused on building an **ETL (Extract, Transform, Load)** pipeline using **Apache Airflow**, **PostgreSQL**, and **Docker**, with automated CI/CD deployments to **Docker Hub**. The objective of the pipeline is to automate the process of extracting data from two sources (RESTful API, SQL database), transforming the data, and loading it into a PostgreSQL database (Analytics DB). The solution is containerized using Docker and managed through Docker-Compose, ensuring seamless execution across various environments while auto-builds and pushes images to **Doker Hub** on code changes.

## Project Structure

The project is organized into the following primary components:

- **DAGs**  Contains the Airflow DAGs (Directed Acyclic Graphs) that define the sequence of operations for the ETL tasks.
- **Docker Compose**: Configuration files for Docker to create containers for PostgreSQL, Airflow, pgAdmin, and other services.
- **Python Scripts**: Custom Python scripts to manage the ingestion, transformation, and loading of data.
- **Airflow Logs**: Airflow logs are stored to track the success or failure of tasks within the ETL process.

## Components

### 1. Docker Containers

The system runs on Docker using the following services:

- **PostgreSQL Database**: The PostgreSQL container serves as the database where the transformed data is loaded.
- **Airflow**: Apache Airflow is used for orchestrating the ETL tasks. It automates the process of fetching data, transforming it, and loading it into PostgreSQL.
- **pgAdmin**: pgAdmin is used as a graphical interface to manage PostgreSQL databases.
- **ETL Application**: A custom Python-based application runs the ETL tasks and interacts with the PostgreSQL database.
- **Jupyter Notebook**: Jupyter is included for data transformation tasks and exploration.

### 2. ETL Process

- **Extract**: Data is extracted from RESTful API and SQL database.
- **Transform**: Data is cleaned, validated, and transformed and normalized into facts and dimension tables.
- **Load**: Transformed data is loaded into the PostgreSQL database (Analytics DB).

### 3. Airflow DAGs

Airflow DAGs define the task execution sequence for the ETL process. The main DAG includes tasks like:

- **Check Staging Files**: Verifies the existence of required staging files.
- **Ingest Data from SQL DB**: Extracts data from SQL databases.
- **Ingest Data from API**: Extracts data from external APIs.
- **Transformation**: Applies transformations to the ingested data.
- **Load Data into PostgreSQL**: Loads the transformed data into the PostgreSQL database.

### 4. Docker Compose

Docker Compose is used to manage the multi-container setup. The setup ensures that all services (PostgreSQL, Airflow, pgAdmin, and Jupyter) are spun up together with proper networking and environment variables. Here's the list of services:

- **PostgreSQL**: The main relational database serving as our data warehouse (Analytics DB).
- **pgAdmin**: A UI to manage and monitor the PostgreSQL database.
- **Airflow**: The orchestration engine running the ETL tasks.
- **ETL App**: Python scripts that perform the ETL operations.
- **Jupyter Notebook**: Data exploration and transformation tasks.

### 5. `.env` File

The `.env` file stores environment-specific variables, including PostgreSQL credentials and Airflow configurations. It ensures sensitive information is kept secure.

## Setup and Installation

To set up and run this project, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/MoraQs/MinifigETLHub.git
```

### 2. Install Docker and Docker Compose

Ensure that Docker and Docker Compose are installed on your system. You can download and install Docker from [here](https://www.docker.com/) and Docker Compose from [here](https://docs.docker.com/compose/install/).

### 3. Configure the `.env` File

Create a `.env` file based on the provided `.env.example` template. The `.env` file contains the database credentials and other configurations.

Example `.env` file:

```bash
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_postgres_db
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=your_postgres_port
```

### 4. Build and Start the Service

After configuring the `.env` file, run the following command to build and start all services using Docker Compose:

```bash
docker-compose up -d --build
```

This will start the PostgreSQL, Airflow, pgAdmin, and other services defined in `docker-compose.yml`.

### 5. Accessing the Services

- **Airflow UI**: You can access the Airflow UI at `http://localhost:8080`.
- **pgAdmin**: Access pgAdmin at `http://localhost:5050`.
- **PostgreSQL**: Connect to PostgreSQL using the credentials in the `.env` file through any PostgreSQL client (pgAdmin, DBeaver, etc.).

## Running the ETL Pipeline

Once the services are up and running, you can trigger the ETL pipeline from the Airflow UI.

### 1. Trigger the DAG

In the Airflow UI, you will see the `full_etl` DAG listed. You can trigger the DAG manually or schedule it to run periodically.

### 2. Monitor Task Execution

Airflow provides detailed logs for each task. You can monitor the execution status, view logs, and debug any issues directly from the Airflow UI.

## Troubleshooting

If you encounter issues, check the following:

- **Logs**: View the logs in Airflow UI or use `docker logs <container_name>` to inspect logs for each.
- **Database Connectivity:**: Ensure that the PostgreSQL container is up and running, and that the connection details are correct.
- **File Paths:**: Double-check the paths to staging files if the ETL process is failing to find or load data.

## CI/CD Pipeline

- **Trigger**: Pushes to `main` branch or version tags (`v*.*.*`)
- **Actions**:
  - Build Docker image from `Dockerfile`
  - Tag with: `latest`, Git SHA (e.g., `1ba4ert`), and semantic versions (e.g., `v1.0.0`)
  - Pushes to [Docker Hub](https://hub.docker.com/)
- **Requirements**:
  - Docker Hub credentials stored in GitHub Secrets
  - Versioned releases via `git tag -a v1.0.0 -m "Release"`

### Why This Matters

- **Reproducibility**: Versioned images ensure consistent deployments.

- **Automation**: No manual builds required after code updates.

- **Traceability**: Git commits map directly to Docker tags.

To customize the pipeline, edit `.github/workflows/ci-cd.yml`.
