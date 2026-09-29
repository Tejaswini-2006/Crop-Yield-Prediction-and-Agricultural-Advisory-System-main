import joblib
import numpy as np
import os

class PredictionModels:
    def __init__(self):
        self.models_dir = 'models/'
        self.yield_model = None
        self.disease_model = None
        self.weather_model = None
        self.fertilizer_recommender = None
        self.load_models()
    
    def load_models(self):
        """Load all trained models cleanly"""
        # Load yield prediction model
        try:
            yield_path = os.path.join(self.models_dir, 'yield_prediction_model.pkl')
            scaler_path = os.path.join(self.models_dir, 'yield_scaler.pkl')
            if os.path.exists(yield_path) and os.path.exists(scaler_path):
                self.yield_model = joblib.load(yield_path)
                self.yield_scaler = joblib.load(scaler_path)
        except Exception as e:
            print(f"Yield model load warning: {e}")

        # Load disease prediction model
        try:
            disease_path = os.path.join(self.models_dir, 'disease_prediction_model.pkl')
            if os.path.exists(disease_path):
                self.disease_model = joblib.load(disease_path)
                self.disease_scaler = joblib.load(os.path.join(self.models_dir, 'disease_scaler.pkl'))
                self.disease_encoder = joblib.load(os.path.join(self.models_dir, 'disease_encoder.pkl'))
        except Exception as e:
            print(f"Disease model load warning: {e}")

        # Load weather model
        try:
            weather_path = os.path.join(self.models_dir, 'weather_model.pkl')
            if os.path.exists(weather_path):
                self.weather_model = joblib.load(weather_path)
        except Exception as e:
            print(f"Weather model load warning: {e}")

        # Load fertilizer recommender
        try:
            fert_path = os.path.join(self.models_dir, 'fertilizer_recommender.pkl')
            if os.path.exists(fert_path) and os.path.getsize(fert_path) > 100:
                self.fertilizer_recommender = joblib.load(fert_path)
        except Exception as e:
            print(f"Fertilizer recommender load warning: {e}")
    
    def predict_yield(self, rainfall, pesticide, temperature):
        """Predict crop yield"""
        if self.yield_model and self.yield_scaler:
            input_data = np.array([[rainfall, pesticide, temperature]])
            input_scaled = self.yield_scaler.transform(input_data)
            prediction = self.yield_model.predict(input_scaled)[0]
            return round(prediction, 2)
        return None
    
    def predict_disease_risk(self, rainfall, temperature, pesticide):
        """Predict disease risk"""
        if self.disease_model and self.disease_scaler and self.disease_encoder:
            input_data = np.array([[rainfall, temperature, pesticide]])
            input_scaled = self.disease_scaler.transform(input_data)
            prediction = self.disease_model.predict(input_scaled)[0]
            risk_level = self.disease_encoder.inverse_transform([prediction])[0]
            return risk_level
        return None
    
    def recommend_fertilizer(self, crop, rainfall):
        """Get fertilizer recommendation"""
        if self.fertilizer_recommender:
            npk, matched_crop = self.fertilizer_recommender(crop, rainfall)
            return {
                'matched_crop': matched_crop,
                'nitrogen_kg_ha': npk['N'],
                'phosphorus_kg_ha': npk['P'],
                'potassium_kg_ha': npk['K'],
                'recommendation': f"Apply {npk['N']}kg/ha N, {npk['P']}kg/ha P, {npk['K']}kg/ha K"
            }
        return None
    
    def predict_weather(self, year):
        """Predict weather patterns"""
        if self.weather_model:
            prediction = self.weather_model.predict(np.array([[year]]))[0]
            return round(prediction, 1)
        return None
