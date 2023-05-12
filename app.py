from flask import Flask, request
import pandas as pd
import random

app = Flask(__name__)
url = 'https://drive.google.com/file/d/1V7Jzs1DV89tqQ4B35dcm_l88atnsNXXJ/view?usp=share_link'
url = 'https://drive.google.com/uc?id=' + url.split('/')[-2]
data = pd.read_csv(url)


@app.route('/', methods=['GET', 'POST'])  # this is the home page route
def hello_world(
):  # this is the home page function that generates the page code

  #req = request.get_json(silent=True, force=True)
  #session = req.get("session")

  #print(req)
  #print(type(req.get('queryResult').get('parameters').get('symptom')))
  #query_result = req.get('parameters')
  #print(query_results)

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

  print('Length of yes_no ', len(yes_no))
  if len(yes_no) == 0:
    index = ''

  message = 'Thank you for your response. Let"s analyse your situation more.'

  print(symptom)
  if len(symptom) == 0:
    message = "I am unable to understand your query. Tell me how you are feeling."

  else:

    # Lower case all symptoms
    symptom = [s.lower() for s in symptom]

    # Search symptom in data
    contains_all_symptoms = data['all_symptoms'].apply(
      lambda x: all(csymptom in x for csymptom in symptom))

    #if len(data[contains_all_symptoms]) == 0:
    #  message = 'I am unable to come on any conclusion on this. Please visit "https://www.google.com/search?q=' + ','.join(symptom)+'"'

    if len(data[contains_all_symptoms]) == 0 and len(symptom) < 5:
      message = 'I am not able to understand from your query. Could you please describe more symptoms on what you are feeling. (fever, headche)'
      symptom = []
      # new_symptoms = []

    elif len(data[contains_all_symptoms]) > 0:

      if len(str(index)) > 0:
        index = int(index)
      else:
        index = random.randint(0, len(data[contains_all_symptoms]) - 1)

      print(len(data[contains_all_symptoms]))
      print(index)

      allSymptoms = data[contains_all_symptoms].iloc[index][[
        'symptoms_1', 'symptoms_2', 'symptoms_3', 'symptoms_4', 'symptoms_5'
      ]].values
      result = data[contains_all_symptoms].iloc[index][[
        'conclusion', 'treatment'
      ]].values

      new_symptoms = [i for i in allSymptoms if i not in symptom]

      if (len(new_symptoms) > 0 and yes_no == 'yes') or len(new_symptoms) == 0:
        message = 'Ok. As per my analysis you may be experiencing ' + result[
          0] + '. Not to worry as the treatment of same is ' + result[1]
        symptom = []
        new_symptoms = []
        index = 0

      elif len(new_symptoms) > 0 and yes_no == 'no':
        message = 'In that case you may be experiencing on of this conditions:'
        for i in data[contains_all_symptoms][['conclusion',
                                              'treatment']].values:
          message += u'\u2029' + f' | Condition - {i[0]} and treatement is {i[1]} '
        symptom = []
        new_symptoms = []
        index = 0

      elif len(symptom) == 5:
        message = 'Ok. As per my analysis you may be experiencing ' + result[
          0] + '. Not to worry as the treatment of same is ' + result[1]
        symptom = []
        new_symptoms = []
        index = 0

      else:
        new_symptoms = [i for i in allSymptoms if i not in symptom]
        message = 'Are you also feeling ' + ', '.join(
          new_symptoms) + '. (Yes/No)'

    else:
      message = 'I am unable to come on any conclusion on this. Please visit "https://www.google.com/search?q=' + ','.join(
        symptom) + '"'
      symptom = []
      new_symptoms = []
      index = 0

  return {
    "fulfillmentText":
    message,
    "outputContexts": [{
      'name': session + '/contexts/symptom_context',
      'lifespanCount': 15,
      'parameters': {
        'identified': symptom,
        'new_symptoms': new_symptoms,
        'index': index
      }
    }],
    "source":
    "webhookdata"
  }


if __name__ == '__main__':
  app.run(host='0.0.0.0',
          port=8080)  # This line is required to run Flask on repl.it
