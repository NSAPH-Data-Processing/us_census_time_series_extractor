FROM condaforge/mambaforge:23.3.1-1

# install build essentials
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

# Clone the repository
#ARG GITHUB_TOKEN
#RUN git clone https://${GITHUB_TOKEN}@github.com/NSAPH-Data-Processing/census .
RUN git clone https://github.com/Climate-CAFE/census_series.git .
RUN mamba env update -n base -f requirements.yml 

# Update snakemake and pulp
#RUN conda install pulp -c conda-forge

# Create paths to data placeholders
RUN python utils/create_data_symlinks.py

# Set the entrypoint to use the Conda environment

#ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "census_series", "snakemake"]
ENTRYPOINT [ "snakemake" ]
CMD ["--cores", "1"]
