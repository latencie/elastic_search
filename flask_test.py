from flask import Flask, render_template, request

app = Flask(__name__, static_url_path='')

@app.route("/")
def index():    
    return render_template('index.html') 

@app.route('/', methods=['GET', 'POST'])
def my_form_post():

    text = request.form['text']
    results = text.split(' ')
    return render_template('resultpage.html', results=results)

if __name__ == "__main__":
    app.run()