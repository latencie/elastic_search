from flask import Flask, render_template, request

app = Flask(__name__, static_url_path='')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'search' in request.form:
        text = request.form['query']
        results = text.split(' ')
        if text == '':
            results = ['Please ask us something!']
        
        return render_template('resultpage.html', results=results)

    if 'advanced' in request.form:
        return render_template('advanced_search.html')

    return render_template('index.html') 

if __name__ == "__main__":
    app.run()