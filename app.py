from flask import Flask, render_template
from flask_assets import Environment, Bundle

app = Flask(__name__)
assets = Environment(app)

# Configuration du bundle SCSS
scss = Bundle('scss/styles.scss', filters='libsass', output='css/styles.css')
assets.register('scss_all', scss)
@app.route('/')
def hello_name():
   return render_template('access.html')

@app.route('/login')
def login():
   return render_template('login.html')

@app.route('/ranking')
def ranking():
   return render_template('ranking.html')

@app.route('/menu')
def menu():
   return render_template('menu.html')

@app.route('/games')
def games():
   return render_template('games.html')

@app.route('/game-party')
def gameparty():
   return render_template('game-party.html')

@app.route('/score')
def score():
   return render_template('score.html')
@app.route('/players')
def players():
   return render_template('players.html')
@app.route('/admins')
def admins():
   return render_template('admins.html')

@app.route('/player-score')
def playerScore():
   return render_template('player-score.html')

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)