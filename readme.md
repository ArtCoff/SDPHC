# SDPHC:A Software for Detecting Petroleum Hydrocarbons Contamination using Non-invasive Survey Dataset

## Usage

Instructions for using the software can be found in the docs directory.

## Features that have been developed:

- [x] Empirical Threshold Analysis
- [x] Background Level Analysis
- [x] Principal Component Analysis
- [x] Auto Report English Version
- [ ] Binary Compiled Version

## Software deployment

(1) In order to run and edit the project properly, you should first clone the project locally: run

```bash
git clone https://github.com/ArtCoff/SDPHC.git
```

(2) Build your python environment from the requirements.yml in your project, using conda is recommended, you can start by editing the first line of the file and changing the name parameter to create an appropriate virtual environment name. Then run

```bash
conda env create -f requirements.yml
```

Of course you can build your own python environment, there is no mandatory dependency on python version.

(3) Just run the main.py file in the app directory.
