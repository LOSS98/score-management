from flask import Flask, render_template
from flask_assets import Environment, Bundle

app = Flask(__name__)
assets = Environment(app)

# Configuration du bundle SCSS
scss = Bundle('scss/styles.scss', filters='libsass', output='css/styles.css')
assets.register('scss_all', scss)
@app.route('/hello/<name>')
def hello_name(name):
   return render_template('index.html', name=name)

if __name__ == '__main__':
   app.run()