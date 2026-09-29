// Main JavaScript for AgriPredict - Fixed Version
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Fixed counter animation for stats
    initializeCounterAnimation();
    
    // Prediction form handlers
    initializePredictionForms();
});

function initializeCounterAnimation() {
    const counters = document.querySelectorAll('[data-count]');
    
    // Only proceed if counters exist
    if (counters.length === 0) {
        return;
    }

    // Check for IntersectionObserver support
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.getAttribute('data-count'), 10);
                    
                    if (isNaN(target)) {
                        counter.innerText = '0';
                        observer.unobserve(counter);
                        return;
                    }

                    let count = 0;
                    const increment = Math.ceil(target / 100);
                    const duration = 2000; // 2 seconds
                    const stepTime = duration / 100;

                    function updateCounter() {
                        count += increment;
                        if (count < target) {
                            counter.innerText = count;
                            setTimeout(updateCounter, stepTime);
                        } else {
                            counter.innerText = target;
                        }
                    }
                    
                    updateCounter();
                    observer.unobserve(counter);
                }
            });
        }, {
            threshold: 0.5
        });

        counters.forEach(counter => observer.observe(counter));
    } else {
        // Fallback for browsers without IntersectionObserver
        counters.forEach(counter => {
            const target = counter.getAttribute('data-count') || '0';
            counter.innerText = target;
        });
    }
}

function initializePredictionForms() {
    // Yield Prediction Form
    const yieldForm = document.getElementById('yield-prediction-form');
    if (yieldForm) {
        yieldForm.addEventListener('submit', handleYieldPrediction);
    }

    // Disease Prediction Form
    const diseaseForm = document.getElementById('disease-prediction-form');
    if (diseaseForm) {
        diseaseForm.addEventListener('submit', handleDiseasePrediction);
    }

    // Fertilizer Recommendation Form
    const fertilizerForm = document.getElementById('fertilizer-form');
    if (fertilizerForm) {
        fertilizerForm.addEventListener('submit', handleFertilizerRecommendation);
    }

    // Weather Prediction Form
    const weatherForm = document.getElementById('weather-form');
    if (weatherForm) {
        weatherForm.addEventListener('submit', handleWeatherPrediction);
    }

    // Crop Recommendation Form
    const cropRecommendationForm = document.getElementById('crop-recommendation-form');
    if (cropRecommendationForm) {
        cropRecommendationForm.addEventListener('submit', handleCropRecommendation);
    }
}

// Enhanced fetch function with proper error handling
async function enhancedFetch(url, options) {
    try {
        const response = await fetch(url, options);
        
        // Check if response is ok (status 200-299)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Fetch failed:', error);
        return { success: false, error: error.message };
    }
}

async function handleYieldPrediction(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = {
        crop: formData.get('crop'),
        rainfall: formData.get('rainfall'),
        pesticide: formData.get('pesticide'),
        temperature: formData.get('temperature')
    };

    showLoading('yield-loading');
    hideResult('yield-result');

    const result = await enhancedFetch('/api/predict-yield', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (result.success && result.data.success) {
        const prediction = result.data;
        showResult('yield-result', 'success', `
            <h5><i class="fas fa-chart-line me-2"></i>Yield Prediction Results</h5>
            <p><strong>Crop:</strong> ${prediction.crop}</p>
            <p><strong>Predicted Yield:</strong> ${prediction.prediction} hg/ha</p>
            <p><strong>Recommendation:</strong> ${getYieldRecommendation(prediction.prediction)}</p>
        `);
    } else {
        const errorMessage = result.data?.error || result.error || 'Unknown error occurred';
        showResult('yield-result', 'danger', 'Error: ' + errorMessage);
    }

    hideLoading('yield-loading');
}

async function handleDiseasePrediction(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = {
        crop: formData.get('crop'),
        rainfall: formData.get('rainfall'),
        temperature: formData.get('temperature'),
        humidity: formData.get('humidity'),
        pesticide: formData.get('pesticide') || 100
    };

    showLoading('disease-loading');
    hideResult('disease-result');

    const result = await enhancedFetch('/api/predict-disease', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (result.success && result.data.success) {
        const prediction = result.data;
        const riskColor = getRiskColor(prediction.risk_level);
        showResult('disease-result', 'success', `
            <h5><i class="fas fa-bug me-2"></i>Disease Risk Assessment</h5>
            <p><strong>Risk Level:</strong> <span class="badge bg-${riskColor}">${prediction.risk_level}</span></p>
            <p><strong>Recommendation:</strong> ${prediction.recommendation}</p>
            <div class="mt-3">
                <small class="text-muted">Based on current environmental conditions and crop type.</small>
            </div>
        `);
    } else {
        const errorMessage = result.data?.error || result.error || 'Unknown error occurred';
        showResult('disease-result', 'danger', 'Error: ' + errorMessage);
    }

    hideLoading('disease-loading');
}

async function handleFertilizerRecommendation(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = {
        crop: formData.get('crop'),
        rainfall: formData.get('rainfall'),
        soil_type: formData.get('soil_type'),
        field_size: formData.get('field_size') || 1.0,
        growth_stage: formData.get('growth_stage'),
        ph_level: formData.get('ph_level')
    };

    showLoading('fertilizer-loading');
    hideResult('fertilizer-result');

    const result = await enhancedFetch('/api/recommend-fertilizer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (result.success && result.data.success) {
        const fertilizer = result.data.fertilizer;
        const fieldSize = result.data.field_size;
        
        let resultHtml = `
            <h5><i class="fas fa-flask me-2"></i>Fertilizer Recommendation for ${fertilizer.matched_crop}</h5>
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="text-center p-4 bg-success bg-opacity-10 rounded-3">
                        <i class="fas fa-leaf fa-2x text-success mb-2"></i>
                        <h6>Nitrogen (N)</h6>
                        <h3 class="text-success">${fertilizer.nitrogen_kg_ha}</h3>
                        <small>kg/ha</small>
                        ${fieldSize > 1 ? `<br><small class="text-muted">Total: ${fertilizer.total_nitrogen_kg} kg</small>` : ''}
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-4 bg-warning bg-opacity-10 rounded-3">
                        <i class="fas fa-seedling fa-2x text-warning mb-2"></i>
                        <h6>Phosphorus (P)</h6>
                        <h3 class="text-warning">${fertilizer.phosphorus_kg_ha}</h3>
                        <small>kg/ha</small>
                        ${fieldSize > 1 ? `<br><small class="text-muted">Total: ${fertilizer.total_phosphorus_kg} kg</small>` : ''}
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-4 bg-info bg-opacity-10 rounded-3">
                        <i class="fas fa-tint fa-2x text-info mb-2"></i>
                        <h6>Potassium (K)</h6>
                        <h3 class="text-info">${fertilizer.potassium_kg_ha}</h3>
                        <small>kg/ha</small>
                        ${fieldSize > 1 ? `<br><small class="text-muted">Total: ${fertilizer.total_potassium_kg} kg</small>` : ''}
                    </div>
                </div>
            </div>`;

        // Add additional information if available
        if (fertilizer.application_schedule) {
            resultHtml += `
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card border-0 bg-light">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0"><i class="fas fa-calendar-alt me-2"></i>Application Schedule</h6>
                            </div>
                            <div class="card-body">
                                <p class="small">${fertilizer.application_schedule.schedule || 'Apply as per standard practices'}</p>
                            </div>
                        </div>
                    </div>
                </div>`;
        }

        resultHtml += `
            <div class="mt-4">
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Important Notes:</strong>
                    <ul class="mt-2 mb-0">
                        <li>These are general recommendations. Always conduct soil testing for precise needs.</li>
                        <li>Apply fertilizers based on weather conditions and soil moisture.</li>
                        <li>Consider organic alternatives and integrated nutrient management.</li>
                        <li>Consult local agricultural experts for region-specific advice.</li>
                    </ul>
                </div>
            </div>`;

        showResult('fertilizer-result', 'success', resultHtml);
    } else {
        const errorMessage = result.data?.error || result.error || 'Unknown error occurred';
        showResult('fertilizer-result', 'danger', 'Error: ' + errorMessage);
    }

    hideLoading('fertilizer-loading');
}

async function handleWeatherPrediction(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = {
        year: formData.get('year'),
        location: formData.get('location')
    };

    showLoading('weather-loading');
    hideResult('weather-result');

    const result = await enhancedFetch('/api/predict-weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (result.success && result.data.success) {
        const prediction = result.data;
        showResult('weather-result', 'success', `
            <h5><i class="fas fa-cloud-sun me-2"></i>Weather Forecast</h5>
            <p><strong>Year:</strong> ${prediction.year}</p>
            <p><strong>Location:</strong> ${prediction.location}</p>
            <p><strong>Predicted Rainfall:</strong> ${prediction.predicted_rainfall} mm</p>
            <div class="alert alert-info mt-3">
                <i class="fas fa-info-circle me-2"></i>
                ${prediction.advice}
            </div>
        `);
    } else {
        const errorMessage = result.data?.error || result.error || 'Unknown error occurred';
        showResult('weather-result', 'danger', 'Error: ' + errorMessage);
    }

    hideLoading('weather-loading');
}

async function handleCropRecommendation(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = {
        rainfall: formData.get('rainfall'),
        temperature: formData.get('temperature'),
        humidity: formData.get('humidity'),
        soil_type: formData.get('soil_type'),
        ph_level: formData.get('ph_level'),
        season: formData.get('season'),
        farm_size: formData.get('farm_size'),
        water_availability: formData.get('water_availability'),
        experience_level: formData.get('experience_level'),
        market_preference: formData.get('market_preference')
    };

    showLoading('crop-loading');
    hideResult('crop-result');

    const result = await enhancedFetch('/api/recommend-crop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    if (result.success && result.data.success) {
        let resultHtml = `
            <h5><i class="fas fa-seedling me-2"></i>Crop Recommendations for Your Farm</h5>
            <div class="alert alert-info mt-3">
                <strong>Analysis Parameters:</strong> 
                Rainfall: ${result.data.parameters_used.rainfall}mm, 
                Temperature: ${result.data.parameters_used.temperature}°C, 
                Soil: ${result.data.parameters_used.soil_type}, 
                Season: ${result.data.parameters_used.season}
            </div>
            <div class="row mt-4">`;

        result.data.recommendations.forEach((crop, index) => {
            const badgeClass = crop.level_class;
            const cardClass = index < 3 ? 'border-success' : 'border-light';
            
            resultHtml += `
                <div class="col-lg-6 mb-4">
                    <div class="card h-100 ${cardClass}">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${crop.crop_name}</h6>
                            <span class="badge bg-${badgeClass}">${crop.suitability_score}% Match</span>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <strong class="text-${badgeClass}">${crop.recommendation_level}</strong>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-6">
                                    <small class="text-muted">Expected Yield</small><br>
                                    <strong>${crop.estimated_yield.per_hectare.toLocaleString()} ${crop.estimated_yield.unit}/ha</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Investment</small><br>
                                    <strong>₹${crop.investment_needed.per_hectare.toLocaleString()}/ha</strong>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-6">
                                    <small class="text-muted">Duration</small><br>
                                    <span>${crop.duration}</span>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Profit Potential</small><br>
                                    <span class="badge bg-info">${crop.profit_potential.replace('_', ' ')}</span>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <small class="text-muted">Market Type:</small> ${crop.market_type}<br>
                                <small class="text-muted">Water Need:</small> ${crop.water_requirement}
                            </div>
                            
                            <div class="mt-3">
                                <button class="btn btn-sm btn-outline-primary" onclick="toggleDetails('details-${index}')">
                                    <i class="fas fa-info-circle"></i> View Details
                                </button>
                            </div>
                            
                            <div id="details-${index}" class="mt-3" style="display: none;">
                                <h6>Suitability Analysis:</h6>
                                <ul class="list-unstyled small">`;
            
            crop.details.forEach(detail => {
                resultHtml += `<li>${detail}</li>`;
            });
            
            if (crop.special_notes && crop.special_notes.length > 0) {
                resultHtml += `</ul>
                                <h6>Special Notes:</h6>
                                <ul class="list-unstyled small">`;
                crop.special_notes.forEach(note => {
                    resultHtml += `<li><i class="fas fa-lightbulb text-warning me-1"></i> ${note}</li>`;
                });
            }
            
            resultHtml += `</ul></div></div></div></div>`;
        });

        resultHtml += `</div>
            <div class="alert alert-warning mt-4">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Important Notes:</strong>
                <ul class="mt-2 mb-0">
                    <li>These recommendations are based on general agricultural guidelines and AI analysis</li>
                    <li>Consider local market conditions and demand before final crop selection</li>
                    <li>Consult local agricultural extension officers for region-specific advice</li>
                    <li>Soil testing is recommended for precise nutrient management</li>
                    <li>Weather conditions can significantly impact actual yields</li>
                </ul>
            </div>`;

        showResult('crop-result', 'success', resultHtml);
    } else {
        const errorMessage = result.data?.error || result.error || 'Unknown error occurred';
        showResult('crop-result', 'danger', 'Error: ' + errorMessage);
    }

    hideLoading('crop-loading');
}

// Utility functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function showResult(elementId, type, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.className = `alert alert-${type} fade-in`;
        element.innerHTML = content;
        element.style.display = 'block';
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideResult(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function getYieldRecommendation(yield) {
    if (yield > 40000) {
        return "Excellent yield expected! Continue current practices and consider premium crop varieties.";
    } else if (yield > 25000) {
        return "Good yield potential. Consider optimizing fertilizer application and irrigation.";
    } else if (yield > 15000) {
        return "Moderate yield expected. Review soil health and consider soil amendments.";
    } else {
        return "Below average yield predicted. Consult agricultural experts for soil and crop management advice.";
    }
}

function getRiskColor(riskLevel) {
    switch(riskLevel.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function toggleDetails(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.style.display === 'none') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Add input event listeners for real-time validation
document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.hasAttribute('required') && this.value.trim()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
});
