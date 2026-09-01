from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='../templates')

# Load external API Keys
recipe_api_key = os.environ.get("RECIPE_API_Key")

# Initialize Groq client
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    client = None
    print(f"Warning: Groq client failed to initialize. Check GROQ_API_KEY. Error: {e}")

@app.route('/')
def home():
    """Renders the main landing page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Renders the main dashboard and configurator."""
    return render_template('dashboard.html')

@app.route('/learn')
def learn():
    """Renders the educational page on sports nutrition and macros."""
    return render_template('learn.html')

@app.route('/api/nutrition', methods=['POST'])
def nutrition_calculator():
    """Handles generation of athlete meal plans and macros."""
    if not client:
        return jsonify({"error": "LLM client not configured. Missing API key."}), 500
        
    data = request.json
    
    prompt = (
        rf"Act as an expert sports nutritionist. Calculate the estimated daily calories and specific macros "
        rf"(protein, carbohydrates, fat, and vegetables) per meal for an athlete with the following profile: "
        rf"Sex: {data.get('sex')}, Height: {data.get('height')}, Weight: {data.get('weight')} lbs, Age: {data.get('age')}, "
        rf"Sport: {data.get('sport')}, Activity Level: {data.get('activityLevel')}, "
        rf"Goal: {data.get('goal')}, Dietary Restrictions: {data.get('restrictions')}. "
        rf"Use their sex, height, weight, and age to accurately calculate their Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation and Total Daily Energy Expenditure (TDEE). "
        rf"Plan their 3 meals and 2 snacks taking their activity level and specific goals into account. "
        rf"Provide exact mealand snack suggestions and you MUST include actual, working markdown links to recipes online "
        rf"for these meals and snacks. Format the entire response in clean Markdown."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced sports nutrition AI. "
                        "STRICT FORMATTING RULE: NEVER use LaTeX code, backslashes (like \\text, \\times), or bracketed math notations (like [ ... ]). "
                        "Write all calculations, formulas, and math strictly in plain text using normal characters and standard symbols (e.g., use 'BMR = (10 * weight) + (6.25 * height) - (5 * age) - 161' and '*' for multiplication, never LaTeX commands)."
                    )
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="openai/gpt-oss-120b", 
            temperature=0.7,
            max_tokens=7500
        )
        return jsonify({"result": chat_completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workout', methods=['POST'])
def workout_generator():
    """Handles generation of sport-specific workouts based on equipment, intensity, injuries, and benchmarks."""
    if not client:
        return jsonify({"error": "LLM client not configured. Missing API key."}), 500
        
    data = request.json
    sport = data.get('sport', 'General Athletics')
    body_part = data.get('bodyPart', '').strip()
    equipment = data.get('equipment', 'None / Bodyweight')
    duration = data.get('duration', '45')
    intensity = data.get('intensity', 'Moderate')
    injuries = data.get('injuries', '').strip()
    benchmarks = data.get('benchmarks', '').strip()
    
    focus_instruction = (
        f"The athlete specifically wants to target and focus on their {body_part} for this session. "
        if body_part 
        else "Focus on a balanced session utilizing sport-specific movements. "
    )
    
    intensity_instruction = (
        f"The user has requested a 'Stretching Only' session. Focus entirely on mobility, flexibility, and recovery for {duration} minutes, ignoring traditional strength sets/reps. "
        if intensity == 'Stretching Only'
        else f"The desired intensity level is: {intensity}. Scale the sets, reps, and pacing for a {duration}-minute session accordingly. "
    )

    injury_instruction = (
        f"CRITICAL: The athlete has the following injuries or limitations: '{injuries}'. You MUST tailor the exercise selection to accommodate this and ensure the movements are safe and will not exacerbate the condition. "
        if injuries and injuries.lower() != 'none'
        else ""
    )

    benchmark_instruction = (
        f"The athlete's current fitness benchmarks/stats are: '{benchmarks}'. Tailor the difficulty, weight recommendations, and progression of the workout to perfectly match this baseline. "
        if benchmarks and benchmarks.lower() != 'none'
        else ""
    )
    
    prompt = (
        rf"Act as an elite strength and conditioning coach. Create a {duration}-minute sport-specific workout for an athlete who plays {sport}. "
        f"{intensity_instruction}"
        f"{focus_instruction}"
        f"{injury_instruction}"
        f"{benchmark_instruction}"
        rf"Equipment available: {equipment}. Ensure the workout relies ONLY on this equipment (or bodyweight if none is specified). "
        rf"Provide a comprehensive routine including a dynamic warmup, a main workout block, and a cooldown. "
        rf"IMPORTANT: You must include step-by-step instructions on how to properly perform each individual exercise. "
        rf"At the very end of the workout, you MUST include a dedicated section reminding the user to refuel and hydrate. "
        rf"Briefly explain how this routine translates to improved performance in {sport}. "
        rf"Format the entire response in Markdown."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional athletic performance and conditioning AI coach. "
                        "STRICT FORMATTING RULE: NEVER use LaTeX code or backslashes. Output all numbers and plain text formulas directly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="openai/gpt-oss-120b",
            temperature=0.6,
            max_tokens=7500
        )
        return jsonify({"result": chat_completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)