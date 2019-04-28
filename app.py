from flask import Flask, jsonify
from util.bot.OgameBot import OgameBot

bot = OgameBot('simonegioele92@gmail.com', 'Simo2000', 'Galatea', '')
app = Flask(__name__)


@app.route('/planets')
def get_planets():
    return jsonify(bot.fetch_planets())


@app.route('/')
def home():
    return "Hello I'm a Bot!"


if __name__ == '__main__':
    app.run()
