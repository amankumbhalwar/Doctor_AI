from flask import Flask, request
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

app = Flask(__name__)
url = 'https://drive.google.com/file/d/1V7Jzs1DV89tqQ4B35dcm_l88atnsNXXJ/view?usp=share_link'
url = 'https://drive.google.com/uc?id=' + url.split('/')[-2]
data = pd.read_csv(url)

# Preprocess data
features = data[['symptoms_1', 'symptoms_2', 'symptoms_3', 'symptoms_4', 'symptoms_5']]
targets = data[['conclusion', 'treatment']]

# Perform one-hot encoding on categorical variables
encoder = OneHotEncoder()
features_encoded = encoder.fit_transform(features).toarray()

# Create Random Forest classifier
rf = RandomForestClassifier()
rf.fit(features_encoded, targets)

@app.route('/', methods=['GET', 'POST'])  # this is the home page route
def hello_world():  # this is the home page function that generates the page code
    return "Data loaded " + str(len(data))

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    session = req.get("session")

    new_symptoms = req.get('queryResult').get('parameters').get('new_symptoms')
    yes_no = req.get('queryResult').get('parameters').get('yes_no')
    index = req.get('queryResult').get('parameters').get('index')

    symptom = req.get('queryResult').get('parameters').get('symptom')
    identified = req.get('queryResult').get('parameters').get('identified')

    symptom.extend(identified)
    symptom = list(set(symptom))

    if len(yes_no) == 0:
        index = ''

    message = 'Thank you for your response. Let\'s analyze your situation further.'

    if len(symptom) == 0:
        message = "I am unable to understand your query. Tell me how you are feeling."
    else:
        symptom_encoded = encoder.transform([symptom]).toarray()

        contains_all_symptoms = (features_encoded == symptom_encoded).all(axis=1)

        if len(data[contains_all_symptoms]) == 0 and len(symptom) < 5:
            message = 'I am unable to understand from your query. Could you please describe more symptoms? (e.g., fever, headache)'
            symptom = []
        elif len(data[contains_all_symptoms]) > 0:
            if len(str(index)) > 0:
                index = int(index)
            else:
                index = random.randint(0, len(data[contains_all_symptoms]) - 1)

            allSymptoms = data[contains_all_symptoms].iloc[index][['symptoms_1', 'symptoms_2', 'symptoms_3', 'symptoms_4', 'symptoms_5']].values
            result = data[contains_all_symptoms].iloc[index][['conclusion', 'treatment']].values

            new_symptoms_encoded = [i for i in allSymptoms if i not in symptom]
            new_symptoms_encoded = encoder.transform([new_symptoms_encoded]).toarray()

            if (len(new_symptoms_encoded) > 0 and yes_no == 'yes') or len(new_symptoms_encoded) == 0:
                message = 'Ok. According to my analysis, you may be experiencing ' + result[0] + '. The treatment for this condition is ' + result[1]
                symptom = []
                new_symptoms = []
                index = 0
            elif len(new_symptoms_encoded) > 0 and yes_no == 'no':
                message = 'In that case, you may be experiencing one of the following conditions:'
                for i in data[contains_all_symptoms][['conclusion', 'treatment']].values:
                    message += '\nCondition: ' + i[0] + ', Treatment: ' + i[1]
                symptom = []
                new_symptoms = []
                index = 0
            elif len(symptom) == 5:
                message = 'Ok. According to my analysis, you may be experiencing ' + result[0] + '. The treatment for this condition is ' + result[1]
                symptom = []
                new_symptoms = []
                index = 0
            else:
                new_symptoms_encoded = [i for i in allSymptoms if i not in symptom]
                new_symptoms_encoded = encoder.transform([new_symptoms_encoded]).toarray()
                message = 'Are you also feeling ' + ', '.join(new_symptoms_encoded) + '? (Yes/No)'
        else:
            message = 'I am unable to come to any conclusion based on your query. Please visit "https://www.google.com/search?q=' + ','.join(symptom) + '"'
            symptom = []
            new_symptoms = []
            index = 0

    return {
        "fulfillmentText": message,
        "outputContexts": [{
            'name': session + '/contexts/symptom_context',
            'lifespanCount': 15,
            'parameters': {
                'identified': symptom,
                'new_symptoms': new_symptoms,
                'index': index
            }
        }],
        "source": "webhookdata"
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

