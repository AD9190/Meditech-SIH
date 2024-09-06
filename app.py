from flask import Flask, request, g
from flask_restful import Resource, Api
import pandas as pd
import spacy
from sqlalchemy import create_engine, text

app = Flask(__name__)
api = Api(app)

# Load the SpaCy model
nlp = spacy.load('en_core_web_sm')

# OTC medications list
otc_medications = ['Aspirin', 'Antacids', 'Ibuprofen', 'Acetaminophen', 'Omeprazole']

# Database setup
DATABASE_URL = "sqlite:///medical_summaries.db"
engine = create_engine(DATABASE_URL)

# Helper functions
def filter_otc_medications(meds_str):
    meds = meds_str.split(', ')
    serious_meds = [med for med in meds if med.split(' ')[0] not in otc_medications]
    if not serious_meds:
        return "otc"
    return ', '.join(serious_meds)

def filter_medications(meds):
    meds = meds.split(', ')
    filtered_meds = []
    for med in meds:
        if any(med in other and med != other for other in meds):
            continue
        filtered_meds.append(med)
    return ', '.join(filtered_meds)

def get_latest_lab_results(lab_results):
    lab_result_dict = {}
    for result in lab_results.split(', '):
        if ': ' in result:
            test, value = result.split(': ', 1)
            lab_result_dict[test] = value  # Overwrite with the latest value
    return ', '.join(f'{test}: {value}' for test, value in lab_result_dict.items())

class PatientSummary(Resource):
    def post(self):
        patient_data = {
            'patientID': request.json.get('patientID'),
            'Name': request.json.get('Name'),
            'Age': int(request.json.get('Age')),
            'Gender': request.json.get('Gender'),
            'visit_date': request.json.get('visit_date'),
            'end_date': request.json.get('end_date'),
            'medical_notes': request.json.get('medical_notes'),
            'diagnosis': request.json.get('diagnosis'),
            'medications': request.json.get('medications'),
            'lab_results': request.json.get('lab_results')
        }

        df = pd.DataFrame([patient_data])

        summary = df.groupby('patientID').agg({
            'Name': 'first',
            'Age': 'last',
            'Gender': 'first',
            'visit_date': 'first',
            'end_date': 'last',
            'diagnosis': lambda x: ', '.join(set(', '.join(x).split(', '))),
            'medications': lambda x: filter_otc_medications(filter_medications(', '.join(set(', '.join(x).split(', '))))),
            'lab_results': lambda x: get_latest_lab_results(', '.join(x))
        }).reset_index()

        summary.to_sql('summaries', con=engine, if_exists='append', index=False)

        return {"message": "Summary added successfully"}, 201

class SummariesList(Resource):
    def get(self):
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM summaries"))
            summaries = [dict(zip(result.keys(), row)) for row in result]
        return summaries, 200

# Add resources to the API
api.add_resource(PatientSummary, '/submit')
api.add_resource(SummariesList, '/summaries')

if __name__ == '__main__':
    app.run(debug=True)