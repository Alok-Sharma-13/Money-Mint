from flask import Flask, render_template, request, flash, redirect
import easyocr
import os
import re
import logging

# Initialize Flask app and EasyOCR reader
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages
reader = easyocr.Reader(['en'])

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    return render_template('ocr.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.warning("No file part in the request.")
        flash('No file uploaded', 'error')
        return redirect('/')

    file = request.files['file']
    if file.filename == '':
        logging.warning("No file selected.")
        flash('No file selected', 'error')
        return redirect('/')

    # Save the uploaded file
    file_path = os.path.join('uploads', file.filename)
    try:
        file.save(file_path)
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        flash('Error saving file', 'error')
        return redirect('/')

    # Perform OCR and calculate carbon footprint
    try:
        results = reader.readtext(file_path)
        extracted_data = process_results(results)
        category_counts = calculate_category_counts(extracted_data)
        total_carbon = calculate_carbon_footprint(extracted_data)  # Calculate carbon footprint
    except Exception as e:
        logging.error(f"Error during OCR processing: {e}")
        flash('Error during OCR processing', 'error')
        return redirect('/')

    return render_template('result.html', extracted_data=extracted_data, category_counts=category_counts, total_carbon=total_carbon)

@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    if request.method == 'POST':
        # Get amounts from form input
        electricity_amount = float(request.form['electricity'])
        transportation_amount = float(request.form['transportation'])
        groceries_amount = float(request.form['groceries'])

        # Calculate carbon footprints for each category
        total_carbon = (
            electricity_amount * 0.5 +
            transportation_amount * 0.2 +
            groceries_amount * 0.1
        )

        return render_template('result_manual.html', total_carbon=total_carbon)

    return render_template('manual_input.html')

# Functions for processing OCR results
def process_results(results):
    categorized_data = {
        'Electricity': [],
        'Transportation': [],
        'Groceries': []
    }

    # Regex to match amounts
    amount_regex = r'(\d+(?:,\d{3})*(?:\.\d{1,2})?)'

    for (bbox, text, prob) in results:
        text = text.strip().lower()

        # Categorize based on keywords in text
        if 'electricity' in text:
            amounts = re.findall(amount_regex, text)
            for amount in amounts:
                categorized_data['Electricity'].append(float(amount.replace(',', '')))
                logging.info(f"Electricity amount identified: {amount}")
                
        elif 'transport' in text or 'transportation' in text:
            amounts = re.findall(amount_regex, text)
            for amount in amounts:
                categorized_data['Transportation'].append(float(amount.replace(',', '')))
                logging.info(f"Transportation amount identified: {amount}")
                
        elif 'grocery' in text or 'groceries' in text:
            amounts = re.findall(amount_regex, text)
            for amount in amounts:
                categorized_data['Groceries'].append(float(amount.replace(',', '')))
                logging.info(f"Groceries amount identified: {amount}")
    
    logging.info(f"Categorized Data: {categorized_data}")
    return categorized_data

def calculate_category_counts(data):
    """Calculate counts for each category."""
    return {
        'Electricity': len(data['Electricity']),
        'Transportation': len(data['Transportation']),
        'Groceries': len(data['Groceries'])
    }

def calculate_carbon_footprint(data):
    """Calculate total carbon footprint based on categorized data."""
    total_carbon = (
        sum(data['Electricity']) * 0.5 +
        sum(data['Transportation']) * 0.2 +
        sum(data['Groceries']) * 0.1
    )
    logging.info(f"Total Carbon Footprint Calculated: {total_carbon}")
    return total_carbon

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True,port=5002)
