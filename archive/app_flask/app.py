from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='Página Inicial')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html', title='Sobre')

if __name__ == '__main__':
    app.run(debug=True)