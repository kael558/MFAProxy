#!/bin/bash
echo "Hello from myscript.sh"

# Create the conda environment
# conda create -n aligner -c conda-forge montreal-forced-aligner

conda activate aligner

# models already downloaded
#mfa model download acoustic english_us_arpa
#mfa model download dictionary english_us_arpa

# Align the data
mfa align --clean inputs/ english_us_arpa english_us_arpa outputs/

conda deactivate