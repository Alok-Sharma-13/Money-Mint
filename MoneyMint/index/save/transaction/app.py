from flask import Flask, render_template, request, flash, redirect, session
import easyocr
import os
import re
import logging
from transformers import pipeline  # For AI integration

# Initialize Flask app and EasyOCR reader
app = Flask(__name__)
app.secret_key = 'ade0245d83c58d65ae5dcef50652a9f6'  # Required for flashing messages
reader = easyocr.Reader(['en'])  # Initialize the EasyOCR reader with English language support

# Initialize the text generation pipeline from Hugging Face
generator = pipeline('text-generation', model='gpt2')  # Load the GPT-2 model for text generation

# Set up logging to track application behavior and errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    """Render the main index page."""
    return render_template('ocr.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and perform OCR on the uploaded file."""
    # Check if the file part exists in the request
    if 'file' not in request.files:
        logging.warning("No file part in the request.")
        flash('No file uploaded', 'error')
        return redirect('/')

    file = request.files['file']  # Get the uploaded file

    # Check if a file has been selected
    if file.filename == '':
        logging.warning("No file selected.")
        flash('No file selected', 'error')
        return redirect('/')

    # Save the uploaded file
    file_path = os.path.join('uploads', file.filename)
    try:
        file.save(file_path)  # Save the uploaded file to the uploads directory
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        flash('Error saving file', 'error')
        return redirect('/')

    # Perform OCR to extract text from the uploaded file
    try:
        results = reader.readtext(file_path)  # Read text from the image
        extracted_data = process_results(results)  # Process the results to categorize data
        category_counts = calculate_category_counts(extracted_data)  # Calculate category counts
    except Exception as e:
        logging.error(f"Error during OCR processing: {e}")
        flash('Error during OCR processing', 'error')
        return redirect('/')

    return render_template('result.html', extracted_data=extracted_data, category_counts=category_counts)

@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    """Handle manual input of carbon footprint data."""
    if request.method == 'POST':
        # Fetch user input for different categories
        try:
            electricity = request.form.get('electricity', type=float)  # Get electricity input
            transportation = request.form.get('transportation', type=float)  # Get transportation input
            groceries = request.form.get('groceries', type=float)  # Get groceries input

            # Initialize total carbon footprint
            total_carbon = 0

            # Calculate carbon footprint for each category if inputs are provided
            if electricity is not None:
                total_carbon += electricity * 0.5  # Example conversion factor

            if transportation is not None:
                total_carbon += transportation * 0.2  # Example conversion factor

            if groceries is not None:
                total_carbon += groceries * 0.1  # Example conversion factor

            # Get AI-generated dynamic advice based on the total carbon footprint
            advice = get_ai_advice(total_carbon)

            return render_template('result_manual.html', total_carbon=total_carbon, advice=advice)
        
        except ValueError as ve:
            logging.error(f"Invalid input: {ve}")
            flash('Please enter valid numeric values.', 'error')
            return redirect('/manual_input')

    return render_template('manual_input.html')  # Render the manual input form
def get_ai_advice(electricity=None, transportation=None, groceries=None):
    """Generate AI-based advice based on the user's carbon footprint inputs."""
    # Prepare the prompt for the AI model
    prompt = "Based on the user's inputs regarding their carbon footprint:\n"

    # Include specific inputs in the prompt
    if electricity is not None:
        prompt += f"- Electricity consumption: {electricity} kWh\n"
    if transportation is not None:
        prompt += f"- Transportation expenses: {transportation} USD\n"
    if groceries is not None:
        prompt += f"- Grocery expenses: {groceries} USD\n"

    # Analyze total carbon based on inputs (use the existing calculation)
    total_carbon = 0
    if electricity is not None:
        total_carbon += electricity * 0.5
    if transportation is not None:
        total_carbon += transportation * 0.2
    if groceries is not None:
        total_carbon += groceries * 0.1

    # Add the total carbon footprint to the prompt
    prompt += f"Total carbon footprint: {total_carbon} kg CO2.\n"
    
    # Instruct the AI to provide personalized advice
    prompt += ("Based on the above information, provide personalized advice on how the user "
               "can reduce their carbon footprint. Make the advice actionable and informative.")

    # Generate advice using the Hugging Face model
    try:
        response = generator(prompt, max_length=150, num_return_sequences=1)[0]['generated_text']
        advice = response.replace(prompt, '').strip()  # Clean the response
    except Exception as e:
        logging.error(f"Error generating AI advice: {e}")
        advice = "There was an issue generating personalized advice. Please try again."

    return advice


def process_results(results):
    """Process OCR results to extract categorized data."""
    categorized_data = {
        'Amounts': []  # Initialize a list to store extracted amounts
    }

    # General number regex (without currency symbols)
    amount_regex = r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)'  # Match numbers formatted as amounts

    for (bbox, text, prob) in results:
        text = text.strip()  # Clean up text

        # Search for amounts in the text
        amount_matches = re.findall(amount_regex, text)
        if amount_matches:
            for amount in amount_matches:
                categorized_data['Amounts'].append(amount.strip())  # Add found amounts to the list

    logging.info(f"Categorized Data: {categorized_data}")
    return categorized_data  # Return the categorized data

def calculate_category_counts(data):
    """Calculate counts based on extracted data."""
    category_counts = {
        'Amounts': len(data['Amounts']),  # Count of extracted amounts
    }
    return category_counts  # Return the counts



if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True,port=5001)  # Run the Flask application in debug mode