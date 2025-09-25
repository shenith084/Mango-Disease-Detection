# config.py
"""
Configuration settings for the Mango Disease Detection API
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek/deepseek-r1-0528:free")

# Rate Limiting Configurations for Different Tiers
RATE_LIMIT_CONFIGS = {
    'free_conservative': {
        'requests_per_minute': 5,
        'requests_per_hour': 40,
        'max_retries': 4,
        'base_delay': 3.0,
        'max_delay': 120.0,
        'timeout': 45,
        'description': 'Ultra-conservative for free tier to avoid rate limits'
    },
    
    'free_standard': {
        'requests_per_minute': 8,
        'requests_per_hour': 60,
        'max_retries': 4,
        'base_delay': 2.5,
        'max_delay': 90.0,
        'timeout': 45,
        'description': 'Standard free tier settings'
    },
    
    'paid_basic': {
        'requests_per_minute': 20,
        'requests_per_hour': 300,
        'max_retries': 3,
        'base_delay': 1.5,
        'max_delay': 30.0,
        'timeout': 30,
        'description': 'Basic paid tier'
    },
    
    'paid_premium': {
        'requests_per_minute': 50,
        'requests_per_hour': 1000,
        'max_retries': 3,
        'base_delay': 1.0,
        'max_delay': 20.0,
        'timeout': 30,
        'description': 'Premium paid tier'
    }
}

# Get current tier from environment
CURRENT_TIER = os.getenv('API_TIER', 'free_conservative').lower()

def get_rate_limit_config():
    """Get the current rate limiting configuration"""
    config = RATE_LIMIT_CONFIGS.get(CURRENT_TIER, RATE_LIMIT_CONFIGS['free_conservative'])
    return config

def get_fallback_responses():
    """Predefined responses when API is unavailable"""
    return {
        'disease_management': """
**Comprehensive Mango Disease Management Guide**

**Common Diseases & Treatment:**

**Anthracnose (Colletotrichum gloeosporioides):**
- Symptoms: Dark, sunken lesions on fruits, leaves, and twigs
- Treatment: Apply copper-based fungicides (Copper sulfate 0.2%) or Propiconazole (0.1%)
- Prevention: Prune for air circulation, remove infected debris

**Alternaria Leaf Spot:**
- Symptoms: Brown spots with yellow halos, concentric rings
- Treatment: Mancozeb (0.25%) or Chlorothalonil (0.2%) spray
- Prevention: Avoid overhead irrigation, maintain plant hygiene

**Black Mould Rot (Aspergillus niger):**
- Symptoms: Black sooty growth during storage
- Treatment: Improve storage ventilation, apply Imazalil (0.05%)
- Prevention: Careful harvesting, proper storage conditions

**Stem End Rot:**
- Symptoms: Brown rot starting from stem end
- Treatment: Post-harvest fungicide dips, controlled atmosphere storage
- Prevention: Proper harvesting techniques, avoid mechanical injury

**Application Guidelines:**
• Apply fungicides during early morning or evening
• Ensure complete coverage of plant surfaces
• Rotate fungicides to prevent resistance
• Follow pre-harvest interval requirements
        """,
        
        'cultivation_practices': """
**Mango Cultivation Best Practices**

**Site Selection & Preparation:**
- Choose well-draining soil with pH 5.5-7.5
- Ensure 6+ hours direct sunlight daily
- Protect from strong winds
- Allow adequate spacing (8-12m between trees)

**Planting Guidelines:**
- Best time: Start of rainy season
- Dig holes 1m x 1m x 1m
- Mix soil with 20-30kg organic matter
- Plant grafted saplings at soil level

**Irrigation Management:**
- Deep, infrequent watering preferred
- Avoid waterlogging during monsoon
- Reduce watering during flowering
- Drip irrigation recommended for efficiency

**Fertilization Schedule:**
- Young trees: 100g N, 50g P, 100g K per year
- Bearing trees: 500g N, 250g P, 500g K per year
- Apply in split doses: pre-monsoon and post-harvest
- Include micronutrients (Zn, B, Mn) annually

**Pruning & Training:**
- Remove dead, diseased, crossing branches
- Maintain 3-4 main scaffolding branches
- Annual pruning after harvest
- Remove water shoots and suckers regularly
        """,
        
        'pest_control': """
**Integrated Mango Pest Management**

**Major Pests & Control:**

**Fruit Flies (Bactrocera dorsalis):**
- Use protein bait traps
- Apply Spinosad (0.02%) or Malathion (0.1%)
- Remove fallen and infested fruits
- Cover developing fruits with paper bags

**Mango Hoppers:**
- Spray Imidacloprid (0.003%) during flowering
- Use sticky traps (yellow/blue)
- Encourage natural predators (spiders, birds)

**Scale Insects:**
- Apply horticultural oil (2%) during dormant season
- Use systemic insecticides (Thiamethoxam 0.004%)
- Scrub off scales manually on small infestations

**Thrips:**
- Blue sticky traps for monitoring
- Spray Fipronil (0.002%) or neem oil (0.5%)
- Maintain field sanitation

**Biological Control:**
- Encourage beneficial insects (ladybirds, lacewings)
- Use pheromone traps for monitoring
- Apply Beauveria bassiana for soil-dwelling pests

**Integrated Approach:**
• Regular monitoring and early detection
• Use economic threshold levels for spraying
• Rotate chemical groups to prevent resistance
• Combine cultural, biological, and chemical methods
        """
    }

# Model Recommendations
MODEL_RECOMMENDATIONS = {
    'free_fast': [
        'meta-llama/llama-3.2-3b-instruct:free',
        'microsoft/phi-3-mini-128k-instruct:free',
        'google/gemma-2-9b-it:free'
    ],
    'free_quality': [
        'deepseek/deepseek-r1-0528:free',
        'meta-llama/llama-3.1-8b-instruct:free',
        'qwen/qwen-2.5-7b-instruct:free'
    ],
    'paid_fast': [
        'anthropic/claude-3-haiku-20240307',
        'openai/gpt-4o-mini',
        'google/gemini-flash-1.5'
    ],
    'paid_quality': [
        'anthropic/claude-3-5-sonnet-20241022',
        'openai/gpt-4o',
        'google/gemini-pro-1.5'
    ]
}

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'manglo_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Flask Configuration
FLASK_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'UPLOAD_FOLDER': 'uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif'}
}

# Model Configuration
MODEL_CONFIG = {
    'IMG_SIZE': (224, 224),
    'DISEASE_CLASSES': ['Alternaria', 'Anthracnose', 'Black Mould Rot', 'Healthy', 'Stem and Rot'],
    'MODEL_PATH': '../Model/best_model_final.h5'
}

# Chat Configuration
CHAT_CONFIG = {
    'MAX_RESPONSE_TOKENS': 2500,
    'TEMPERATURE': 0.7,
    'TOP_P': 0.9,
    'FREQUENCY_PENALTY': 0.1,
    'CONVERSATION_HISTORY_LIMIT': 6
}

def print_current_config():
    """Print current configuration for debugging"""
    config = get_rate_limit_config()
    print(f"Current API Tier: {CURRENT_TIER}")
    print(f"Rate Limits: {config['requests_per_minute']}/min, {config['requests_per_hour']}/hour")
    print(f"Max Retries: {config['max_retries']}")
    print(f"Base Delay: {config['base_delay']}s")
    print(f"Description: {config['description']}")
    print(f"OpenRouter API: {'Configured' if OPENROUTER_API_KEY else 'Not Configured'}")
    print(f"Chat Model: {CHAT_MODEL}")

if __name__ == "__main__":
    print("Configuration Settings:")
    print_current_config()