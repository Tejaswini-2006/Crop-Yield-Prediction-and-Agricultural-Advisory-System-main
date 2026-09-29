"""
AgriPredict Models Package

This package contains all the machine learning models and prediction logic
for the agricultural prediction system.
"""

from .prediction_models import PredictionModels
from .db_models import db, User, PredictionHistory, ForumPost, ForumResponse, MarketListing

__version__ = "1.0.0"
__author__ = "AgriPredict Team"

# Model metadata
MODEL_INFO = {
    "yield_prediction": {
        "name": "Crop Yield Prediction",
        "algorithm": "Random Forest Regressor",
        "accuracy": "95%",
        "features": ["rainfall", "pesticide_usage", "temperature"]
    },
    "disease_prediction": {
        "name": "Disease Risk Assessment",
        "algorithm": "Random Forest Classifier",
        "accuracy": "92%",
        "features": ["rainfall", "temperature", "humidity", "pesticide_usage"]
    },
    "fertilizer_recommendation": {
        "name": "NPK Fertilizer Recommendation",
        "algorithm": "Rule-based System",
        "accuracy": "90%",
        "features": ["crop_type", "rainfall", "soil_type"]
    },
    "weather_prediction": {
        "name": "Weather Pattern Analysis",
        "algorithm": "Linear Regression",
        "accuracy": "85%",
        "features": ["historical_patterns", "seasonal_trends"]
    }
}

def get_model_info(model_name=None):
    """
    Get information about available models
    
    Args:
        model_name (str, optional): Specific model name. If None, returns all models.
    
    Returns:
        dict: Model information
    """
    if model_name:
        return MODEL_INFO.get(model_name, {})
    return MODEL_INFO

def list_available_models():
    """
    List all available prediction models
    
    Returns:
        list: List of model names
    """
    return list(MODEL_INFO.keys())
