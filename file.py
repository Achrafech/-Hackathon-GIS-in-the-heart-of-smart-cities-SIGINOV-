from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index2.html')

@app.route('/', methods=['POST'])
def submit():
    user_input = request.form['user_input']
    with open("values.txt", 'w') as file:
        file.write('X_end , Y_end :'+ user_input + '\n')
    return render_template('index2.html')

@app.route('/save_location', methods=['POST'])
def save_location():
    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']

    with open("values.txt", 'a') as file:
        file.write(f'Latitude START,Longitude START: {latitude},{longitude} \n')

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
