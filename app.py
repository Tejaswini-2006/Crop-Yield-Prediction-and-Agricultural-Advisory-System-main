import os
import json
import random
import string
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
)
from flask_babel import Babel, gettext as _, refresh
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# --- Initialization and Configuration ---

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'agripredict-fallback-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///agripredict.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import Database Models
from models.db_models import db, User, PredictionHistory, ForumPost, ForumResponse, MarketListing
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = _('Please log in to access this page.')
login_manager.login_message_category = 'warning'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables if missing
with app.app_context():
    db.create_all()

# Import Utilities
from utils.leaf_disease_detector import LeafDiseaseDetector
from utils.pdf_generator import PDFReportGenerator

leaf_detector = LeafDiseaseDetector()

# --- BABEL/I18N CONFIGURATION ---
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['LANGUAGES'] = {
    'en': 'English',
    'mr': 'मराठी (Marathi)'
}

babel = Babel() 

def get_locale():
    """Selects the best language based on session or browser preference."""
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(list(app.config['LANGUAGES'].keys()))

babel.init_app(app, locale_selector=get_locale)

# Initialize prediction models
try:
    from models.prediction_models import PredictionModels 
    prediction_models = PredictionModels()
    models_loaded = True
except Exception as e:
    print(f"Error loading prediction models: {e}")
    models_loaded = False
# --- LANGUAGE SWITCH ROUTE ---
@app.route('/set_language/<language>')
def set_language(language):
    """Sets the language preference in the session and redirects back."""
    if language in app.config['LANGUAGES']:
        session['language'] = language
    
    # Force a refresh to apply the new language immediately
    refresh()
    
    # Redirect the user back to the page they were on (request.referrer) or index
    return redirect(request.referrer or url_for('index'))


# --- WEB PAGE ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/yield-prediction')
def yield_prediction():
    return render_template('yield_prediction.html')

@app.route('/disease-prediction')
def disease_prediction():
    return render_template('disease_prediction.html')

@app.route('/fertilizer-recommendation')
def fertilizer_recommendation():
    return render_template('fertilizer_recommendation.html')

@app.route('/weather-prediction')
def weather_prediction():
    return render_template('weather_prediction.html')

@app.route('/crop-recommendation')
def crop_recommendation():
    return render_template('crop_recommendation.html')

@app.route('/leaf-disease-detection')
def leaf_disease_detection():
    return render_template('leaf_disease.html')

# --- AUTHENTICATION & DASHBOARD ROUTES ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        location = request.form.get('location', '').strip()

        if not name or not email or not password:
            flash(_('Please fill in all required fields.'), 'danger')
            return redirect(url_for('signup'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(_('Email address is already registered. Please log in.'), 'warning')
            return redirect(url_for('login'))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            location=location or 'Maharashtra, India'
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(_('Account created successfully! Welcome to AgriPredict.'), 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash(_('Invalid email or password. Please try again.'), 'danger')
            return redirect(url_for('login'))

        login_user(user)
        flash(_('Logged in successfully.'), 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    history_items = PredictionHistory.query.filter_by(user_id=current_user.id).order_by(PredictionHistory.created_at.desc()).all()
    return render_template('dashboard.html', history_items=history_items)

@app.route('/api/delete-history/<int:history_id>', methods=['POST'])
@login_required
def delete_history(history_id):
    history_item = PredictionHistory.query.filter_by(id=history_id, user_id=current_user.id).first()
    if history_item:
        db.session.delete(history_item)
        db.session.commit()
        flash(_('History record deleted successfully.'), 'success')
    else:
        flash(_('Record not found or unauthorized.'), 'danger')
    return redirect(url_for('dashboard'))

@app.route('/api/export-pdf/<int:history_id>')
@login_required
def export_pdf(history_id):
    item = PredictionHistory.query.filter_by(id=history_id, user_id=current_user.id).first_or_404()
    pdf_buffer = PDFReportGenerator.generate_report(
        report_type=item.prediction_type,
        title=item.title,
        input_data=item.get_input_json(),
        result_data=item.get_result_json(),
        farmer_name=current_user.name
    )
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"AgriPredict_{item.prediction_type}_{item.id}.pdf",
        mimetype='application/pdf'
    )

@app.route('/farmer-connect')
def farmer_connect():
    return render_template('farmer_connect.html')

@app.route('/farmer-connect/forum')
def farmer_forum():
    return render_template('farmer_forum.html')

@app.route('/farmer-connect/experts')
def expert_advice():
    return render_template('expert_advice.html')

@app.route('/farmer-connect/marketplace')
def farmer_marketplace():
    return render_template('farmer_marketplace.html')


# --- Helper for Prediction History ---

def save_prediction_history(pred_type, title, input_dict, result_dict):
    if current_user.is_authenticated:
        try:
            history_record = PredictionHistory(
                user_id=current_user.id,
                prediction_type=pred_type,
                title=title,
                input_data=json.dumps(input_dict),
                result_data=json.dumps(result_dict)
            )
            db.session.add(history_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving prediction history: {e}")

# --- API Routes for Predictions ---

@app.route('/api/predict-yield', methods=['POST'])
def api_predict_yield():
    try:
        data = request.json
        rainfall = float(data['rainfall'])
        pesticide = float(data['pesticide'])
        temperature = float(data['temperature'])
        crop = data.get('crop', 'Maize')
        
        if models_loaded:
            yield_pred = prediction_models.predict_yield(rainfall, pesticide, temperature)
            message = _('Predicted yield for %(crop)s: %(yield_pred)s hg/ha', crop=crop, yield_pred=yield_pred)
        else:
            base_yield = 30000
            rain_factor = min(rainfall / 1000, 1.5)
            pest_factor = min(pesticide / 200, 1.2)
            temp_factor = max(0.5, 1 - abs(temperature - 25) / 25) 
            yield_pred = round(base_yield * rain_factor * pest_factor * temp_factor)
            message = _('Estimated yield for %(crop)s: %(yield_pred)s hg/ha', crop=crop, yield_pred=yield_pred)

        # Save to user prediction history
        save_prediction_history(
            pred_type='yield',
            title=f"Yield Estimate: {crop} ({yield_pred} hg/ha)",
            input_dict={'crop': crop, 'rainfall': rainfall, 'pesticide': pesticide, 'temperature': temperature},
            result_dict={'predicted_yield': f"{yield_pred} hg/ha", 'crop': crop}
        )

        return jsonify({
            'success': True,
            'prediction': yield_pred,
            'crop': crop,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/predict-disease', methods=['POST'])
def api_predict_disease():
    try:
        data = request.json
        rainfall = float(data['rainfall'])
        temperature = float(data['temperature'])
        humidity = float(data.get('humidity', 70))
        pesticide = float(data.get('pesticide', 100))
        crop = data.get('crop', 'General Crop')

        if models_loaded:
            disease_risk = prediction_models.predict_disease_risk(rainfall, temperature, pesticide)
        else:
            risk_score = 0
            if rainfall > 1000: risk_score += 2
            elif rainfall > 500: risk_score += 1
            if 15 <= temperature <= 25: risk_score += 2 
            if humidity > 80: risk_score += 1
            if pesticide < 100: risk_score += 1
            
            if risk_score >= 4: disease_risk = _('High')
            elif risk_score >= 2: disease_risk = _('Medium')
            else: disease_risk = _('Low')
        
        recommendations = {
            _('High'): _('Apply fungicide, improve drainage, reduce plant density'),
            _('Medium'): _('Monitor crops closely, ensure proper ventilation'),
            _('Low'): _('Continue regular monitoring, maintain good practices')
        }
        
        rec = recommendations.get(disease_risk, _('Monitor regularly'))

        save_prediction_history(
            pred_type='disease',
            title=f"Disease Risk: {crop} - {disease_risk}",
            input_dict={'crop': crop, 'rainfall': rainfall, 'temperature': temperature, 'humidity': humidity, 'pesticide': pesticide},
            result_dict={'risk_level': disease_risk, 'recommendation': rec}
        )

        return jsonify({
            'success': True,
            'risk_level': disease_risk,
            'recommendation': rec,
            'message': _('Disease risk level: %(risk_level)s', risk_level=disease_risk)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/predict-weather', methods=['POST'])
def api_predict_weather():
    try:
        data = request.json
        year = int(data.get('year', 2025))
        location = data.get('location', 'General')
        
        # Check if live OpenWeatherMap API key is provided in .env
        weather_api_key = os.getenv('OPENWEATHER_API_KEY')
        live_weather = None

        if weather_api_key and location and location != 'General':
            try:
                resp = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric",
                    timeout=4
                )
                if resp.status_code == 200:
                    wdata = resp.json()
                    live_weather = {
                        'temp': wdata['main']['temp'],
                        'humidity': wdata['main']['humidity'],
                        'description': wdata['weather'][0]['description'].title()
                    }
            except Exception as w_err:
                print(f"Live Weather API call skipped: {w_err}")

        if models_loaded:
            rainfall_pred = prediction_models.predict_weather(year)
        else:
            base_rainfall = 800
            year_factor = (year - 2020) * 5
            rainfall_pred = round(base_rainfall + year_factor + random.randint(-50, 50))
        
        if rainfall_pred < 400:
            weather_advice = _("Low rainfall expected. Consider drought-resistant crops and irrigation planning.")
        elif rainfall_pred > 1500:
            weather_advice = _("High rainfall expected. Ensure proper drainage and flood management.")
        else:
            weather_advice = _("Normal rainfall expected. Good conditions for most crops.")
        
        return jsonify({
            'success': True,
            'year': year,
            'location': location,
            'predicted_rainfall': rainfall_pred,
            'live_weather': live_weather,
            'advice': weather_advice,
            'message': _('Weather prediction for %(year)s: %(rainfall_pred)smm rainfall', year=year, rainfall_pred=rainfall_pred)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/recommend-fertilizer', methods=['POST'])
def api_recommend_fertilizer():
    try:
        data = request.json
        crop = data['crop']
        rainfall = float(data['rainfall'])
        soil_type = data.get('soil_type', 'medium')
        field_size = float(data.get('field_size', 1.0))
        growth_stage = data.get('growth_stage', 'vegetative')
        
        recommendation = generate_fallback_fertilizer_recommendation(
            crop, rainfall, soil_type, growth_stage, field_size
        )

        save_prediction_history(
            pred_type='fertilizer',
            title=f"Fertilizer NPK: {crop} ({recommendation['nitrogen_kg_ha']}-{recommendation['phosphorus_kg_ha']}-{recommendation['potassium_kg_ha']})",
            input_dict={'crop': crop, 'rainfall': rainfall, 'soil_type': soil_type, 'field_size': field_size, 'growth_stage': growth_stage},
            result_dict={'N': recommendation['nitrogen_kg_ha'], 'P': recommendation['phosphorus_kg_ha'], 'K': recommendation['potassium_kg_ha'], 'recommendation': recommendation['recommendation']}
        )
        
        return jsonify({
            'success': True,
            'fertilizer': recommendation,
            'field_size': field_size,
            'message': _('Fertilizer recommendation generated successfully'),
            'note': _('Recommendations based on general agricultural guidelines')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': _('Unable to generate recommendation: %(error)s', error=str(e))})


@app.route('/api/recommend-crop', methods=['POST'])
def api_recommend_crop():
    try:
        data = request.json
        rainfall = float(data['rainfall'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        soil_type = data['soil_type']
        ph_level = float(data.get('ph_level', 7.0))
        season = data.get('season', 'kharif')
        farm_size = float(data.get('farm_size', 1.0))
        water_availability = data.get('water_availability', 'moderate')
        experience_level = data.get('experience_level', 'intermediate')
        market_preference = data.get('market_preference', 'food_grain')
        
        recommendations = generate_crop_recommendations(
            rainfall, temperature, humidity, soil_type, ph_level, 
            season, farm_size, water_availability, experience_level, market_preference
        )

        top_crop = recommendations[0]['crop_name'] if recommendations else 'Maize'

        save_prediction_history(
            pred_type='crop',
            title=f"Crop Suitability: Top match - {top_crop}",
            input_dict={'soil_type': soil_type, 'rainfall': rainfall, 'temperature': temperature, 'season': season},
            result_dict={'top_recommendations': [r['crop_name'] for r in recommendations[:3]]}
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'message': _('Crop recommendations generated successfully'),
            'parameters_used': {
                'rainfall': rainfall,
                'temperature': temperature,
                'humidity': humidity,
                'soil_type': soil_type,
                'season': season
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/predict-leaf-disease', methods=['POST'])
def api_predict_leaf_disease():
    try:
        if 'leaf_image' not in request.files:
            return jsonify({'success': False, 'error': _('No image file uploaded.')})
        
        file = request.files['leaf_image']
        if file.filename == '':
            return jsonify({'success': False, 'error': _('No image file selected.')})
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
            file.save(file_path)
            
            analysis = leaf_detector.analyze_image(file_path)
            if analysis.get('success'):
                save_prediction_history(
                    pred_type='leaf_disease',
                    title=f"Leaf Scanner: {analysis['disease_name']}",
                    input_dict={'image': filename},
                    result_dict={'disease': analysis['disease_name'], 'confidence': f"{analysis['confidence']}%", 'status': analysis['status']}
                )
                return jsonify({
                    'success': True,
                    'diagnosis': analysis
                })
            else:
                return jsonify({'success': False, 'error': analysis.get('error', _('Analysis failed'))})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# --- Farmer Connect APIs with Database Persistence ---

@app.route('/api/post-question', methods=['POST'])
def api_post_question():
    try:
        data = request.json
        farmer_name = data.get('farmer_name', current_user.name if current_user.is_authenticated else 'Farmer')
        location = data.get('location', current_user.location if current_user.is_authenticated else 'Maharashtra')
        
        post = ForumPost(
            user_id=current_user.id if current_user.is_authenticated else None,
            farmer_name=farmer_name,
            location=location,
            crop_type=data.get('crop_type', 'General'),
            category=data.get('category', 'General'),
            question=data.get('question', '')
        )
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'question_id': post.id,
            'message': _('Your question has been posted successfully to SQLite DB!'),
            'estimated_response_time': _('2-4 hours')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/get-forum-posts')
def api_get_forum_posts():
    posts_db = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    if not posts_db:
        # Seed mock initial posts into database if empty
        seed_posts = generate_mock_forum_posts()
        for sp in seed_posts:
            fp = ForumPost(
                farmer_name=sp['farmer_name'],
                location=sp['location'],
                crop_type=sp['crop_type'],
                category=sp['category'],
                question=sp['question'],
                status=sp['status']
            )
            db.session.add(fp)
        db.session.commit()
        posts_db = ForumPost.query.order_by(ForumPost.created_at.desc()).all()

    output = []
    for p in posts_db:
        output.append({
            'id': f"Q{p.id:03d}",
            'farmer_name': p.farmer_name,
            'location': p.location,
            'crop_type': p.crop_type,
            'category': p.category,
            'question': p.question,
            'timestamp': p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'responses': len(p.responses),
            'helpful_count': 5,
            'status': p.status
        })

    return jsonify({
        'success': True,
        'posts': output,
        'total_posts': len(output)
    })


@app.route('/api/submit-listing', methods=['POST'])
def api_submit_listing():
    try:
        data = request.json
        listing = MarketListing(
            user_id=current_user.id if current_user.is_authenticated else None,
            farmer_name=data.get('farmer_name', current_user.name if current_user.is_authenticated else 'Farmer'),
            contact=data['contact'],
            location=data['location'],
            listing_type=data['listing_type'],
            item_name=data['item_name'],
            quantity=data['quantity'],
            price=data.get('price', 'Negotiable'),
            description=data.get('description', '')
        )
        db.session.add(listing)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'listing_id': listing.id,
            'message': _('Your listing has been posted successfully to SQLite DB!')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# --- HELPER FUNCTIONS (Integrated Below) ---

def generate_fallback_fertilizer_recommendation(crop, rainfall, soil_type, growth_stage, field_size):
    """
    Generate realistic fertilizer recommendations with random variations
    """
    
    # Base NPK values for different crops (kg/ha)
    crop_npk_base = {
        'Maize': {'N': 120, 'P': 60, 'K': 40},
        'Rice': {'N': 100, 'P': 50, 'K': 50},
        'Potatoes': {'N': 150, 'P': 80, 'K': 120},
        'Soybeans': {'N': 20, 'P': 40, 'K': 60},  # Lower N due to nitrogen fixation
        'Wheat': {'N': 120, 'P': 40, 'K': 30},
        'Sorghum': {'N': 80, 'P': 40, 'K': 40},
        'Cotton': {'N': 120, 'P': 60, 'K': 60},
        'Sugarcane': {'N': 200, 'P': 80, 'K': 100},
        'Tomatoes': {'N': 150, 'P': 100, 'K': 150},
    }
    
    # Find matching crop (case-insensitive, partial matching)
    matched_crop = 'Maize'  # Default
    crop_clean = crop.replace(',', '').replace(' paddy', '').replace('(', '').replace(')', '').strip()
    
    for crop_key in crop_npk_base.keys():
        if crop_key.lower() in crop_clean.lower() or crop_clean.lower() in crop_key.lower():
            matched_crop = crop_key
            break
    
    base_npk = crop_npk_base[matched_crop]
    
    # Rainfall adjustments (Use _() for translation)
    if rainfall < 400: # Low rainfall
        rain_factor_n = random.uniform(1.15, 1.25)
        rain_factor_p = random.uniform(1.10, 1.20)
        rain_factor_k = random.uniform(1.05, 1.15)
        rainfall_note = _("Low rainfall: Increased fertilizer needs")
    elif rainfall > 1500: # High rainfall
        rain_factor_n = random.uniform(0.75, 0.85)
        rain_factor_p = random.uniform(0.80, 0.90)
        rain_factor_k = random.uniform(1.10, 1.20)
        rainfall_note = _("High rainfall: Reduced N&P, increased K for leaching prevention")
    else: # Normal rainfall
        rain_factor_n = random.uniform(0.95, 1.05)
        rain_factor_p = random.uniform(0.95, 1.05)
        rain_factor_k = random.uniform(0.95, 1.05)
        rainfall_note = _("Normal rainfall: Standard fertilizer application")
    
    # Soil type adjustments
    soil_adjustments = {
        'clay': {'N': 0.9, 'P': 1.1, 'K': 0.9},
        'sandy': {'N': 1.1, 'P': 1.2, 'K': 1.1},
        'loamy': {'N': 1.0, 'P': 1.0, 'K': 1.0},
        'silt': {'N': 0.95, 'P': 1.05, 'K': 0.95},
        'red': {'N': 1.05, 'P': 1.15, 'K': 1.0},
        'black': {'N': 0.95, 'P': 0.9, 'K': 1.05}
    }
    
    soil_factor = soil_adjustments.get(soil_type, {'N': 1.0, 'P': 1.0, 'K': 1.0})
    
    # Growth stage adjustments
    stage_adjustments = {
        'pre-sowing': {'N': 0.3, 'P': 0.5, 'K': 0.3},
        'sowing': {'N': 0.4, 'P': 0.6, 'K': 0.4},
        'vegetative': {'N': 1.2, 'P': 0.8, 'K': 0.9},
        'flowering': {'N': 0.6, 'P': 1.2, 'K': 1.1},
        'maturity': {'N': 0.2, 'P': 0.3, 'K': 0.8}
    }
    
    stage_factor = stage_adjustments.get(growth_stage, {'N': 1.0, 'P': 1.0, 'K': 1.0})
    
    # Calculate final NPK values with random variation (±10%)
    final_n = round(base_npk['N'] * rain_factor_n * soil_factor['N'] * stage_factor['N'] * random.uniform(0.9, 1.1))
    final_p = round(base_npk['P'] * rain_factor_p * soil_factor['P'] * stage_factor['P'] * random.uniform(0.9, 1.1))
    final_k = round(base_npk['K'] * rain_factor_k * soil_factor['K'] * stage_factor['K'] * random.uniform(0.9, 1.1))
    
    # Ensure minimum values
    final_n = max(final_n, 10)
    final_p = max(final_p, 5)
    final_k = max(final_k, 5)
    
    # Calculate total amounts for field
    total_n = round(final_n * field_size, 1)
    total_p = round(final_p * field_size, 1)
    total_k = round(final_k * field_size, 1)
    
    # Generate application schedule
    application_schedule = generate_application_schedule(growth_stage, final_n, final_p, final_k)
    
    # Generate fertilizer types
    fertilizer_types = generate_fertilizer_types(final_n, final_p, final_k)
    
    return {
        'matched_crop': matched_crop,
        'nitrogen_kg_ha': final_n,
        'phosphorus_kg_ha': final_p,
        'potassium_kg_ha': final_k,
        'total_nitrogen_kg': total_n,
        'total_phosphorus_kg': total_p,
        'total_potassium_kg': total_k,
        # Use _() for translation
        'recommendation': _("Apply %(n)skg/ha N, %(p)skg/ha P, %(k)skg/ha K for %(crop)s", n=final_n, p=final_p, k=final_k, crop=matched_crop),
        'rainfall_factor': rainfall_note,
        'soil_type': soil_type.title(),
        'growth_stage': growth_stage.replace('_', ' ').title(),
        'application_schedule': application_schedule,
        'fertilizer_types': fertilizer_types,
        'cost_estimate': calculate_fertilizer_cost(final_n, final_p, final_k, field_size)
    }

def generate_application_schedule(growth_stage, n, p, k):
    """Generate application schedule based on growth stage"""
    
    # Use _() for translation on descriptions
    schedules = {
        'pre-sowing': {
            'basal': {'N': 100, 'P': 100, 'K': 100},
            'schedule': _("Apply all fertilizers as basal dose before sowing")
        },
        'sowing': {
            'basal': {'N': 50, 'P': 100, 'K': 50},
            'top_dress_1': {'N': 50, 'P': 0, 'K': 50},
            'schedule': _("50% N&K as basal, 50% N&K after 3-4 weeks. All P as basal.")
        },
        'vegetative': {
            'basal': {'N': 40, 'P': 100, 'K': 40},
            'top_dress_1': {'N': 40, 'P': 0, 'K': 40},
            'top_dress_2': {'N': 20, 'P': 0, 'K': 20},
            'schedule': _("40% N&K basal, 40% at 25 days, 20% at 45 days. All P basal.")
        },
        'flowering': {
            'current': {'N': 30, 'P': 70, 'K': 60},
            'next': {'N': 20, 'P': 30, 'K': 40},
            'schedule': _("Focus on P&K for flower/fruit development. Reduce N.")
        },
        'maturity': {
            'current': {'N': 10, 'P': 20, 'K': 50},
            'schedule': _("Minimal fertilizer. Focus on K for fruit filling.")
        }
    }
    
    return schedules.get(growth_stage, schedules['vegetative'])

def generate_fertilizer_types(n, p, k):
    """Suggest specific fertilizer types"""
    
    fertilizer_options = []
    
    # Nitrogen sources
    n_sources = [_('Urea (46% N)'), _('Ammonium Sulphate (21% N)'), _('CAN (26% N)'), _('DAP (18% N)')]
    fertilizer_options.append({
        'nutrient': _('Nitrogen'),
        'recommended_source': random.choice(n_sources),
        'quantity_needed': f"{round(n/0.46 if 'Urea' in n_sources[0] else n/0.21, 1)} kg/ha"
    })
    
    # Phosphorus sources
    p_sources = [_('DAP (46% P2O5)'), _('SSP (16% P2O5)'), _('TSP (46% P2O5)'), _('Bone Meal (22% P2O5)')]
    fertilizer_options.append({
        'nutrient': _('Phosphorus'),
        'recommended_source': random.choice(p_sources),
        'quantity_needed': f"{round(p/0.46 if 'DAP' in p_sources[0] else p/0.16, 1)} kg/ha"
    })
    
    # Potassium sources
    k_sources = [_('MOP (60% K2O)'), _('SOP (50% K2O)'), _('Potash (50% K2O)'), _('Ash (5% K2O)')]
    fertilizer_options.append({
        'nutrient': _('Potassium'),
        'recommended_source': random.choice(k_sources),
        'quantity_needed': f"{round(k/0.60 if 'MOP' in k_sources[0] else k/0.50, 1)} kg/ha"
    })
    
    return fertilizer_options

def calculate_fertilizer_cost(n, p, k, field_size):
    """Calculate estimated fertilizer cost"""
    
    # Approximate costs per kg of nutrient (in INR)
    n_cost = random.uniform(25, 35)  # per kg N
    p_cost = random.uniform(50, 70)  # per kg P
    k_cost = random.uniform(30, 45)  # per kg K
    
    total_cost = (n * n_cost + p * p_cost + k * k_cost) * field_size
    
    return {
        'per_hectare': round(n * n_cost + p * p_cost + k * k_cost, 2),
        'total_field': round(total_cost, 2),
        'currency': _('INR'),
        'breakdown': {
            'nitrogen_cost': round(n * n_cost * field_size, 2),
            'phosphorus_cost': round(p * p_cost * field_size, 2),
            'potassium_cost': round(k * k_cost * field_size, 2)
        }
    }

def generate_crop_recommendations(rainfall, temperature, humidity, soil_type, ph_level, season, farm_size, water_availability, experience_level, market_preference):
    """
    Generate crop recommendations based on multiple parameters
    """
    
    # Comprehensive crop database with requirements
    crop_database = {
        'Rice': {
            'rainfall': (1000, 2500), 'temperature': (20, 35), 'humidity': (70, 95),
            'soil_types': ['clay', 'loamy', 'alluvial'], 'ph_range': (5.5, 7.0),
            'water_need': 'high', 'season': ['kharif', 'rabi'],
            'experience': ['beginner', 'intermediate', 'advanced'], 'market_type': 'food_grain',
            'yield_potential': 'high', 'investment': 'medium', 'duration': '120-150 days',
            'profit_margin': 'medium'
        },
        'Wheat': {
            'rainfall': (300, 1000), 'temperature': (15, 25), 'humidity': (50, 70),
            'soil_types': ['loamy', 'clay', 'black'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['rabi'],
            'experience': ['beginner', 'intermediate', 'advanced'], 'market_type': 'food_grain',
            'yield_potential': 'high', 'investment': 'medium', 'duration': '120-140 days',
            'profit_margin': 'medium'
        },
        'Maize': {
            'rainfall': (500, 1200), 'temperature': (18, 32), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (5.5, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi', 'zaid'],
            'experience': ['beginner', 'intermediate', 'advanced'], 'market_type': 'food_grain',
            'yield_potential': 'high', 'investment': 'medium', 'duration': '90-120 days',
            'profit_margin': 'high'
        },
        'Cotton': {
            'rainfall': (500, 1200), 'temperature': (21, 35), 'humidity': (60, 85),
            'soil_types': ['black', 'alluvial', 'red'], 'ph_range': (6.0, 8.0),
            'water_need': 'medium', 'season': ['kharif'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'cash_crop',
            'yield_potential': 'high', 'investment': 'high', 'duration': '180-200 days',
            'profit_margin': 'very_high'
        },
        'Sugarcane': {
            'rainfall': (1000, 2000), 'temperature': (20, 35), 'humidity': (70, 90),
            'soil_types': ['loamy', 'clay', 'alluvial'], 'ph_range': (6.0, 7.5),
            'water_need': 'very_high', 'season': ['annual'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'cash_crop',
            'yield_potential': 'very_high', 'investment': 'very_high', 'duration': '12-18 months',
            'profit_margin': 'high'
        },
        'Soybeans': {
            'rainfall': (400, 800), 'temperature': (20, 30), 'humidity': (60, 80),
            'soil_types': ['loamy', 'black', 'red'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['kharif'],
            'experience': ['beginner', 'intermediate'], 'market_type': 'oilseed',
            'yield_potential': 'medium', 'investment': 'low', 'duration': '90-110 days',
            'profit_margin': 'medium'
        },
        'Groundnut': {
            'rainfall': (500, 1000), 'temperature': (20, 30), 'humidity': (65, 85),
            'soil_types': ['sandy', 'red', 'black'], 'ph_range': (6.0, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi'],
            'experience': ['beginner', 'intermediate'], 'market_type': 'oilseed',
            'yield_potential': 'medium', 'investment': 'medium', 'duration': '100-120 days',
            'profit_margin': 'medium'
        },
        'Tomato': {
            'rainfall': (400, 800), 'temperature': (18, 27), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.0),
            'water_need': 'high', 'season': ['rabi', 'zaid'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'vegetable',
            'yield_potential': 'high', 'investment': 'high', 'duration': '90-120 days',
            'profit_margin': 'very_high'
        },
        'Potato': {
            'rainfall': (400, 700), 'temperature': (15, 25), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (5.5, 6.5),
            'water_need': 'medium', 'season': ['rabi'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'vegetable',
            'yield_potential': 'high', 'investment': 'high', 'duration': '90-120 days',
            'profit_margin': 'high'
        },
        'Onion': {
            'rainfall': (300, 600), 'temperature': (15, 25), 'humidity': (60, 70),
            'soil_types': ['loamy', 'sandy', 'alluvial'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['rabi', 'kharif'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'vegetable',
            'yield_potential': 'medium', 'investment': 'medium', 'duration': '120-150 days',
            'profit_margin': 'high'
        },
        'Sunflower': {
            'rainfall': (400, 800), 'temperature': (20, 30), 'humidity': (60, 80),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.5),
            'water_need': 'medium', 'season': ['kharif', 'rabi'],
            'experience': ['beginner', 'intermediate'], 'market_type': 'oilseed',
            'yield_potential': 'medium', 'investment': 'low', 'duration': '90-110 days',
            'profit_margin': 'medium'
        },
        'Chili': {
            'rainfall': (600, 1200), 'temperature': (20, 30), 'humidity': (70, 85),
            'soil_types': ['loamy', 'sandy', 'red'], 'ph_range': (6.0, 7.0),
            'water_need': 'medium', 'season': ['kharif', 'rabi'],
            'experience': ['intermediate', 'advanced'], 'market_type': 'spice',
            'yield_potential': 'high', 'investment': 'medium', 'duration': '150-180 days',
            'profit_margin': 'very_high'
        }
    }
    
    # Score each crop based on suitability
    crop_scores = {}
    
    for crop, requirements in crop_database.items():
        score = 0
        max_score = 100
        details = []
        
        # Rainfall suitability (20 points)
        rain_min, rain_max = requirements['rainfall']
        if rain_min <= rainfall <= rain_max:
            rain_score = 20
            details.append(_("✓ Rainfall requirement met (%(min)s-%(max)smm)", min=rain_min, max=rain_max))
        elif rainfall < rain_min:
            rain_score = max(0, 20 - (rain_min - rainfall) / rain_min * 20)
            details.append(_("⚠ Rainfall slightly low (needs %(min)s-%(max)smm)", min=rain_min, max=rain_max))
        else:
            rain_score = max(0, 20 - (rainfall - rain_max) / rain_max * 20)
            details.append(_("⚠ Rainfall slightly high (optimal: %(min)s-%(max)smm)", min=rain_min, max=rain_max))
        score += rain_score
        
        # Temperature suitability (20 points)
        temp_min, temp_max = requirements['temperature']
        if temp_min <= temperature <= temp_max:
            temp_score = 20
            details.append(_("✓ Temperature requirement met (%(min)s-%(max)s°C)", min=temp_min, max=temp_max))
        elif temperature < temp_min:
            temp_score = max(0, 20 - (temp_min - temperature) / temp_min * 20)
            details.append(_("⚠ Temperature slightly low (needs %(min)s-%(max)s°C)", min=temp_min, max=temp_max))
        else:
            temp_score = max(0, 20 - (temperature - temp_max) / temp_max * 20)
            details.append(_("⚠ Temperature slightly high (optimal: %(min)s-%(max)s°C)", min=temp_min, max=temp_max))
        score += temp_score
        
        # Soil type suitability (15 points)
        if soil_type in requirements['soil_types']:
            soil_score = 15
            details.append(_("✓ Suitable for %(soil_type)s soil", soil_type=soil_type))
        else:
            soil_score = 8
            details.append(_("⚠ Moderately suitable for %(soil_type)s soil", soil_type=soil_type))
        score += soil_score
        
        # pH suitability (10 points)
        ph_min, ph_max = requirements['ph_range']
        if ph_min <= ph_level <= ph_max:
            ph_score = 10
            details.append(_("✓ pH requirement met (%(min)s-%(max)s)", min=ph_min, max=ph_max))
        else:
            ph_score = max(0, 10 - abs(ph_level - (ph_min + ph_max) / 2))
            details.append(_("⚠ pH adjustment may be needed (optimal: %(min)s-%(max)s)", min=ph_min, max=ph_max))
        score += ph_score
        
        # Season suitability (10 points)
        if season in requirements['season'] or 'annual' in requirements['season']:
            season_score = 10
            details.append(_("✓ Suitable for %(season)s season", season=season))
        else:
            season_score = 5
            details.append(_("⚠ Not ideal season (best: %(seasons)s)", seasons=', '.join(requirements['season'])))
        score += season_score
        
        # Experience level (10 points)
        if experience_level in requirements['experience']:
            exp_score = 10
            details.append(_("✓ Suitable for %(level)s farmers", level=experience_level))
        else:
            exp_score = 6
            details.append(_("⚠ May require %(level)s level expertise", level=requirements['experience'][-1]))
        score += exp_score
        
        # Water availability (10 points)
        water_compatibility = {
            'low': ['low', 'medium'],
            'medium': ['low', 'medium', 'high'],
            'high': ['medium', 'high', 'very_high'],
            'very_high': ['high', 'very_high']
        }
        
        if requirements['water_need'] in water_compatibility.get(water_availability, []):
            water_score = 10
            details.append(_("✓ Water requirement compatible"))
        else:
            water_score = 5
            details.append(_("⚠ Water requirement: %(need)s", need=requirements['water_need']))
        score += water_score
        
        # Market preference (5 points)
        if requirements['market_type'] == market_preference or market_preference == 'mixed':
            market_score = 5
            details.append(_("✓ Matches market preference"))
        else:
            market_score = 3
            details.append(_("⚠ Different market category: %(type)s", type=requirements['market_type']))
        score += market_score
        
        # Calculate percentage
        score_percentage = round((score / max_score) * 100, 1)
        
        # Determine recommendation level (Use _() for translation)
        if score_percentage >= 80:
            recommendation_level = _("Highly Recommended")
            level_class = "success"
        elif score_percentage >= 65:
            recommendation_level = _("Recommended")
            level_class = "primary"
        elif score_percentage >= 50:
            recommendation_level = _("Moderately Suitable")
            level_class = "warning"
        else:
            recommendation_level = _("Not Recommended")
            level_class = "danger"
        
        crop_scores[crop] = {
            'score': score_percentage,
            'recommendation_level': recommendation_level,
            'level_class': level_class,
            'details': details,
            'requirements': requirements,
            'estimated_yield': calculate_estimated_yield(crop, score_percentage, farm_size),
            'investment_needed': calculate_investment(crop, farm_size),
            'profit_potential': requirements['profit_margin'],
            'duration': requirements['duration'],
            'special_notes': generate_special_notes(crop, rainfall, temperature, soil_type)
        }
    
    # Sort crops by score
    sorted_crops = sorted(crop_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    
    # Return top recommendations
    return [
        {
            'crop_name': crop,
            'suitability_score': data['score'],
            'recommendation_level': data['recommendation_level'],
            'level_class': data['level_class'],
            'details': data['details'],
            'estimated_yield': data['estimated_yield'],
            'investment_needed': data['investment_needed'],
            'profit_potential': data['profit_potential'],
            'duration': data['duration'],
            'special_notes': data['special_notes'],
            'market_type': data['requirements']['market_type'].replace('_', ' ').title(), 
            'water_requirement': data['requirements']['water_need'].title()
        }
        for crop, data in sorted_crops[:8]  # Top 8 recommendations
    ]

def calculate_estimated_yield(crop, score_percentage, farm_size):
    """Calculate estimated yield based on suitability score"""
    
    base_yields = {
        'Rice': 4000, 'Wheat': 3500, 'Maize': 5000, 'Cotton': 2000,
        'Sugarcane': 80000, 'Soybeans': 2500, 'Groundnut': 2000,
        'Tomato': 40000, 'Potato': 25000, 'Onion': 30000,
        'Sunflower': 1800, 'Chili': 3000
    }
    
    base_yield = base_yields.get(crop, 3000)
    yield_factor = score_percentage / 100
    estimated_yield_per_ha = round(base_yield * yield_factor * random.uniform(0.9, 1.1))
    total_yield = round(estimated_yield_per_ha * farm_size, 1)
    
    return {
        'per_hectare': estimated_yield_per_ha,
        'total_farm': total_yield,
        # Use _() for translation
        'unit': _('kg') if crop != 'Sugarcane' else _('tons') 
    }

def calculate_investment(crop, farm_size):
    """Calculate investment requirements"""
    
    investment_per_ha = {
        'Rice': random.randint(25000, 35000),
        'Wheat': random.randint(20000, 30000),
        'Maize': random.randint(15000, 25000),
        'Cotton': random.randint(30000, 45000),
        'Sugarcane': random.randint(80000, 120000),
        'Soybeans': random.randint(12000, 18000),
        'Groundnut': random.randint(18000, 25000),
        'Tomato': random.randint(40000, 60000),
        'Potato': random.randint(35000, 50000),
        'Onion': random.randint(25000, 35000),
        'Sunflower': random.randint(10000, 15000),
        'Chili': random.randint(20000, 30000)
    }
    
    per_ha = investment_per_ha.get(crop, 20000)
    total = round(per_ha * farm_size)
    
    return {
        'per_hectare': per_ha,
        'total_farm': total,
        'currency': _('INR')
    }

def generate_special_notes(crop, rainfall, temperature, soil_type):
    """Generate special notes and tips for each crop"""
    notes = []
    
    # Use _() for translation on tips
    crop_tips = {
        'Rice': [_("Ensure proper water management"), _("Consider SRI method for better yields")],
        'Wheat': [_("Apply nitrogen in split doses"), _("Monitor for rust diseases")],
        'Maize': [_("Maintain proper plant spacing"), _("Good for intercropping")],
        'Cotton': [_("Monitor for bollworm attacks"), _("Requires skilled labor")],
        'Sugarcane': [_("Long-term crop commitment"), _("High water requirement")],
        'Soybeans': [_("Natural nitrogen fixation"), _("Good rotation crop")],
        'Tomato': [_("Requires staking and pruning"), _("High market demand")],
        'Potato': [_("Cool storage needed"), _("Good processing potential")],
        'Onion': [_("Long shelf life"), _("Export potential")],
        'Chili': [_("High value spice crop"), _("Processing opportunities")]
    }
    
    if crop in crop_tips:
        notes.extend(crop_tips[crop])
    
    # Add weather-specific notes (Use _() for translation)
    if rainfall > 1500:
        notes.append(_("High rainfall - ensure good drainage"))
    elif rainfall < 400:
        notes.append(_("Low rainfall - plan irrigation carefully"))
    
    if temperature > 35:
        notes.append(_("High temperature - consider shade nets"))
    elif temperature < 15:
        notes.append(_("Low temperature - may need protection"))
    
    return notes

# Helper functions for Farmer Connect
def generate_question_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_listing_id():
    return 'LST' + ''.join(random.choices(string.digits, k=6))

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_mock_forum_posts():
    # Mock data should also have translatable strings in a real-world scenario
    
    posts = [
        {
            'id': 'Q001', 'farmer_name': 'Rajesh Kumar', 'location': 'Punjab', 'crop_type': 'Wheat',
            'category': _('Disease Management'),
            'question': _('My wheat crop is showing yellow rust symptoms. What immediate action should I take?'),
            'timestamp': (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            'responses': 3, 'helpful_count': 12, 'status': _('answered')
        },
        {
            'id': 'Q002', 'farmer_name': 'Priya Sharma', 'location': 'Maharashtra', 'crop_type': 'Cotton',
            'category': _('Pest Control'),
            'question': _('How to control bollworm attack in cotton without using excessive pesticides?'),
            'timestamp': (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
            'responses': 7, 'helpful_count': 25, 'status': _('answered')
        },
        {
            'id': 'Q004', 'farmer_name': 'Lakshmi Devi', 'location': 'Andhra Pradesh', 'crop_type': 'Rice',
            'category': _('Water Management'),
            'question': _('How to implement drip irrigation system for paddy cultivation?'),
            'timestamp': (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            'responses': 1, 'helpful_count': 3, 'status': _('open')
        },
    ]
    return posts

def generate_nearby_farmers(location, crop_interest):
    
    farmers = [
        {
            'name': 'Amit Singh', 'location': location, 'crops': ['Wheat', 'Mustard', 'Barley'],
            'experience': _('15 years'), 'specialization': _('Organic farming'),
            'contact': '+91 98xxx-xxxxx', 'rating': 4.8, 'distance': f"{random.randint(2, 15)} km"
        },
        {
            'name': 'Sunita Devi', 'location': location, 'crops': ['Rice', 'Vegetables', 'Pulses'],
            'experience': _('12 years'), 'specialization': _('Sustainable agriculture'),
            'contact': '+91 97xxx-xxxxx', 'rating': 4.6, 'distance': f"{random.randint(5, 20)} km"
        },
        {
            'name': 'Kiran Patil', 'location': location, 'crops': ['Cotton', 'Soybean', 'Maize'],
            'experience': _('20 years'), 'specialization': _('Precision farming'),
            'contact': '+91 96xxx-xxxxx', 'rating': 4.9, 'distance': f"{random.randint(8, 25)} km"
        },
    ]
    
    if crop_interest != 'All':
        farmers = [f for f in farmers if crop_interest in f['crops']]
    
    return random.sample(farmers, min(len(farmers), 6))

# --- Execution ---

if __name__ == '__main__':
    # Using the host and port settings provided in the final execution block
    app.run(debug=True, host='0.0.0.0', port=5000)