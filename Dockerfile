FROM condaforge/mambaforge:23.3.1-1

# install build essentials
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

ARG GITHUB_TOKEN

# Clone your repository
RUN git clone https://${GITHUB_TOKEN}@github.com/NSAPH-Data-Processing/census .

# Copy requirements.yml into the container
COPY requirements.yml .

# Create a new Conda environment using the requirements.yml file
RUN mamba env create -f requirements.yml

# Activate the new environment for subsequent commands
SHELL ["conda", "run", "-n", "census_acs5_env", "/bin/bash", "-c"]

# Create paths to data placeholders
RUN python utils/create_data_symlinks.py

# Set the entrypoint to use the Conda environment
ENTRYPOINT ["conda", "run", "-n", "census_acs5_env", "bash", "-c", "source activate census_acs5_env && snakemake --configfile conf/config.yaml"]
CMD ["--cores", "1"]
