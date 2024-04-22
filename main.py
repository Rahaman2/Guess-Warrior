from flask import Flask, render_template

app = Flask(__name__, template_folder='views/templates')

# Import your controllers
from controllers import *

if __name__ == '__main__':
    app.run(debug=True)