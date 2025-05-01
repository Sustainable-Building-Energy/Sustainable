# Sustainable

This is the code repository for the Sustainable Energy course class project. 

The main entry points for each section of the project are as follows:

|Section|File|
|---|---|
|LA Demand: |[LADWP_electricity.ipynb](LADWP_electricity.ipynb)  |
|Wind: | [suse/wind/wind_calc.py](suse/wind/wind_calc.py)  |
|Solar: |[notebooks/1.0-nrel_solar_api.ipynb](notebooks/1.0-nrel_solar_api.ipynb)  |
|Economics: |[notebooks/2.0-economic.ipynb](notebooks/2.0-economic.ipynb)|

# Requirements
Refer to the list of packages in [environment.yml](environment.yml). 

To utilize the NREL API, please register for an api key. Then create a file with the fullname `.env` in the top folder of this repo with the following contents:
```
NREL_API_KEY="your_api_key"
EMAIL="your_email@gmail.com"
```

# Installation

To create a development environment with the required packages run the following command:
```
conda env create -f environment.yml
```
To install the suse package after cloning the repo, run the following command in the home folder of the repo:
```
pip install -e .
```
or install from online:
```
pip install git+https://github.com/Sustainable-Building-Energy/Sustainable.git
```
*Note: some there may be some hard coded paths that need to be changed in order to make the code work on your system.*


