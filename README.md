# Crop Yield Prediction and Agricultural Advisory System

## Project Overview

This project implements an Agricultural Prediction System using Flask, machine learning models, and rule-based systems to provide valuable insights for farmers. It offers functionalities for crop yield prediction, disease risk assessment, fertilizer recommendation, and weather pattern analysis. The system is designed to aid in informed decision-making to optimize agricultural practices and improve productivity.

## Features

- **Crop Yield Prediction**: Predicts crop yield based on environmental factors like rainfall, pesticide usage, and temperature using a Random Forest Regressor.
- **Disease Risk Assessment**: Assesses the risk of crop diseases based on environmental conditions (rainfall, temperature, pesticide usage) using a Random Forest Classifier.
- **Fertilizer Recommendation**: Provides rule-based recommendations for NPK (Nitrogen, Phosphorus, Potassium) fertilizers tailored to specific crops, rainfall, soil types, and growth stages.
- **Weather Pattern Analysis**: Analyzes historical weather data and provides future rainfall predictions using a Linear Regression model, along with general weather advice.
- **Interactive Web Interface**: A user-friendly web application built with Flask for easy interaction with the prediction models.

## Project Structure

```
Crop Yield Prediction/
├── app.py                      # Main Flask application file
├── dataset/                    # Stores raw and processed agricultural data
│   ├── pesticides.csv
│   ├── rainfall.csv
│   ├── temp.csv
│   ├── yield_df.csv
│   └── yield.csv
├── models/                     # Contains trained machine learning models and scalers
│   ├── disease_encoder.pkl
│   ├── disease_prediction_model.pkl
│   ├── disease_scaler.pkl
│   ├── fertilizer_recommender.pkl # This file is expected by app.py but not explicitly saved in training.ipynb. The system uses a rule-based fallback if not found.
│   ├── __init__.py
│   ├── prediction_models.py    # Class to load and use prediction models
│   ├── weather_model.pkl
│   ├── yield_prediction_model.pkl
│   └── yield_scaler.pkl
├── requirements.txt            # Python dependencies
├── static/                     # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── charts.js
│       └── main.js
├── templates/                  # HTML templates for the web application
│   ├── about.html
│   ├── base.html
│   ├── disease_prediction.html
│   ├── fertilizer_recommendation.html
│   ├── index.html
│   ├── weather_prediction.html
│   └── yield_prediction.html
└── training.ipynb              # Jupyter notebook for data analysis, model training, and evaluation
```

## Setup Instructions

To get this project up and running on your local machine, follow these steps:

### 1. Clone the Repository

```bash
git clone <repository_url>
cd "Crop Yield Prediction"
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

- **On Windows:**
  ```bash
  .\venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Train the Models (if not already trained)

The trained models are included in the `models/` directory. However, if you wish to retrain them or understand the training process, run the `training.ipynb` Jupyter notebook.

```bash
jupyter notebook training.ipynb
```
Follow the steps in the notebook to execute all cells. This will preprocess the data, train the models, and save them to the `models/` directory.

### 6. Run the Flask Application

```bash
python app.py
```

The application will typically run on `http://127.0.0.1:5000/`. Open this URL in your web browser.

## Usage

Once the Flask application is running, you can navigate through the different sections of the web interface:

- **Home (`/`)**: Overview of the project.
- **About (`/about`)**: Information about the project.
- **Crop Yield Prediction (`/yield-prediction`)**: Input environmental parameters to get a yield prediction.
- **Disease Prediction (`/disease-prediction`)**: Get a disease risk assessment based on environmental conditions.
- **Fertilizer Recommendation (`/fertilizer-recommendation`)**: Receive NPK fertilizer recommendations for your crops.
- **Weather Prediction (`/weather-prediction`)**: Get rainfall predictions for a given year.

API endpoints are also available for programmatic access:
- `POST /api/predict-yield`
- `POST /api/predict-disease`
- `POST /api/recommend-fertilizer`
- `POST /api/predict-weather`

Refer to the `app.py` file for the exact request payload and response structure for each API endpoint.

## Technologies Used

- **Backend**: Flask
- **Machine Learning**: scikit-learn, joblib, numpy, pandas
- **Data Visualization**: matplotlib, seaborn
- **Frontend**: HTML, CSS, JavaScript

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to open an issue or submit a pull request. 