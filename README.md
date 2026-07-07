# Quantum Yield Calculator
V1 - User Friendly Version - A Streamlit web app for calculating absorbed photons and quantum yield from absorbance and LED emission data (python version)

V2 - Single Submission - A html web link for calculating absorbed photons and quantum yield from absorbance and LED emission data (javascript version).

## Features
- Upload absorbance Excel files
- Upload LED emission Excel files
- Calculate extinction coefficient
- Scale absorbance to new conditions
- Baseline and normalize LED spectra
- Fit Gaussian curves to LED emission
- Calculate photon metrics
- Calculate absorption efficiency
- Calculate quantum yields

## Required file format
Both uploaded Excel files should have:
- Column 1: wavelength
- Column 2: measurement values

## Run locally (Streamlit, User Friendly Version
```bash
pip install -r requirements.txt
streamlit run app.py
