# Skin Clinic Campaign Analysis API

FastAPI application analysing a 10,000-customer skin clinic marketing campaign.
Built for Module 10 Assignment 1 (Model Deployment Using FastAPI).

## Files

|File|What it is|
|-|-|
|`main.py`|The FastAPI application|
|`skin\_clinic\_campaign.csv`|The campaign dataset|
|`requirements.txt`|Python packages Render needs to install|
|`render.yaml`| Render |

## Endpoints

|Endpoint|What it returns|
|-|-|
|`/campaign-analysis`|The four analysis tables as HTML |
|`/campaign-analysis/json`|JSON|
|`/health`|Health check, used by Render|
|`/docs`|Interactive Swagger documentation |
|`/`|Landing page linking to the above|

## Running it on your own machine

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open [http://127.0.0.1:8000/campaign-analysis](http://127.0.0.1:8000/campaign-analysis).

## 

