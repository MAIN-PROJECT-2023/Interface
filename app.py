from flask import Flask, render_template, request, jsonify,url_for, redirect, url_for, session,flash,abort
import random
import json
import pickle
import numpy as np
from markupsafe import Markup



import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model 



from flask_pymongo import PyMongo
from flask_wtf import FlaskForm, csrf
from pymongo import MongoClient


from functools import wraps



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


mode='cloud'
if mode=='local':
    # Connect to MongoDB
    app.config['MONGO_URI']= 'mongodb://localhost:27017/chatbot'
else:
    # Connect to MongoDB
    app.config['MONGO_URI']='mongodb+srv://shiban:hqwaSJns8vkQVVtk@cluster0.6dhrc7h.mongodb.net/test'

mongo = PyMongo(app)
db = mongo.db


lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.keras')


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    if intents_list:
        tag = intents_list[0]['intent']
        # Rest of your code here
    else:
        # Handle the case when the list is empty
        tag = "I'm sorry, I didn't quite catch that. Can you please provide more details or ask another question?"

    list_of_intents = intents_json['intents']
    result = "I'm sorry, I didn't quite catch that. Can you please provide more details or ask another question?"  # Set a default response in case the tag is not found
    for i in list_of_intents:
        if i.get('tag') == tag:
            result = random.choice(i.get('responses', ["Default response"]))
            break

    return result


print("GO! Bot is running!")  



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('loginregpage'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/loginregpage')
def loginregpage():
    return render_template('login.html')



@app.route("/register-success", methods=['POST'])
def homeregister():
    if request.method == 'POST':
        name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("new-password")
        confirmpwd = request.form.get("confirm-password")

        if not name or not email or not password or not confirmpwd:
            flash('All fields are required', 'error')
            return redirect(url_for('loginregpage'))

        if password != confirmpwd:
            flash('Passwords do not match', 'error')
            return redirect(url_for('loginregpage'))

        if db.chatbotuser.find_one({'email': email}):
            flash('Email already exists', 'error')
            return redirect(url_for('loginregpage'))

        db.chatbotuser.insert_one({'name': name, 'email': email, 'password': password})

        # Store user information in session after registration
        session['user'] = {'name': name, 'email': email}
        
        flash('Registration successful', 'success')
        return redirect(url_for('chatbotpage', username=name))

    return render_template('login.html')

@app.route("/login", methods=['POST'])
def logincred():
    if request.method == 'POST':
        email = request.form.get("email1")
        password = request.form.get("password")

        if not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('loginregpage'))

        user = db.chatbotuser.find_one({'email': email, 'password': password})

        if user:
            # Extract the first name from the 'name' field
            full_name = user.get('name', '')
            if full_name and len(full_name.split()[0]) == 1:
                # If the first name is an initial, get the second name
                second_name = ' '.join(full_name.split()[1:])
                first_name = second_name if second_name else ''
            else:
                # If the first name is not an initial, get the first name
                first_name = full_name.split()[0] if full_name else ''

            # Store user ID and first name in session
            session['user'] = {'name': first_name, 'email': email}
            flash('Login successful', 'success')

            # Redirect to chatbotpage with the username in the URL
            return redirect(url_for('chatbotpage', username=first_name))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('loginregpage'))




@app.route('/chatbotpage')
@login_required
def chatbotpage():
    # Retrieve user information from session
    user = session.get('user', None) 

    # Check if user is logged in
    if user:
        # Pass the username to the template
        return render_template('chatbot.html', username=user['name'])
    else:
        # Redirect to login page if not logged in
        flash('Please log in first', 'error')
        return redirect(url_for('loginregpage'))


@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.form['user_message']
    ints = predict_class(user_message)
    res = get_response(ints, intents)
    return jsonify({'bot_response': res, 'user_message': user_message})





    

@app.route('/aptitude')
@login_required
def aptitude():
    return render_template('/testAptitude/demo.html')


@app.route('/submit_form', methods=['POST'])
@login_required
def submit_form():
    education = request.form['education']
    print("Education selected:", education)

    # Redirect based on education type
    if education == "10th":
        return redirect(url_for('tenth'))
    elif education == "12th":
        return redirect(url_for('twelth'))
    elif education == "Higher":
        return redirect(url_for('higher'))
    else:
        return "Invalid education type", 400

@app.route('/tenth')
@login_required
def tenth():
    return render_template('/Highschool/tenth.html')

@app.route('/twelth')
@login_required
def twelth():
    return render_template('/Highschool/Hss/twelth.html')

@app.route('/higher')
@login_required
def higher():
    return render_template('/Highschool/proff/proof.html')


@app.route('/quantitative10')
@login_required
def quantitative_test10():
    # Render the template for the quantitative test
    return render_template('/Highschool/num10.html')

@app.route('/abstract10')
@login_required
def abstract_test10():
    # Render the template for the abstract test
    return render_template('/Highschool/ar10.html')

@app.route('/verbal10')
@login_required
def verbal_test10():
    # Render the template for the verbal test
    return render_template('/Highschool/verb10.html')

@app.route('/spatial10')
@login_required
def spatial_test10():
    # Render the template for the spatial test
    return render_template('/Highschool/sp10.html')

@app.route('/mechanical10')
@login_required
def mechanical_test10():
    # Render the template for the mechanical test
    return render_template('/Highschool/mech10.html')

@app.route('/perceptual10')
@login_required
def perceptual_test10():
    # Render the template for the perceptual test
    return render_template('/Highschool/per10.html')

@app.route('/language10')
@login_required
def language_test10():
    # Render the template for the language test
    return render_template('/Highschool/lang10.html')





@app.route('/quantitativeH')
@login_required
def quantitative_testH():
    # Render the template for the quantitative test
    return render_template('/Highschool/Hss/num12.html')

@app.route('/abstractH')
@login_required
def abstract_testH():
    # Render the template for the abstract test
    return render_template('/Highschool/Hss/ar12.html')

@app.route('/verbalH')
@login_required
def verbal_testH():
    # Render the template for the verbal test
    return render_template('/Highschool/Hss/verb12.html')

@app.route('/spatialH')
@login_required
def spatial_testH():
    # Render the template for the spatial test
    return render_template('/Highschool/Hss/sp12.html')

@app.route('/mechanicalH')
@login_required
def mechanical_testH():
    # Render the template for the mechanical test
    return render_template('/Highschool/Hss/mech12.html')

@app.route('/perceptualH')
@login_required
def perceptual_testH():
    # Render the template for the perceptual test
    return render_template('/Highschool/Hss/per12.html')

@app.route('/languageH')
@login_required
def language_testH():
    # Render the template for the language test
    return render_template('/Highschool/Hss/lang12.html')




if __name__ == '__main__':
    app.run(debug=True)