import scrapper
from flask import Flask, send_from_directory, abort
from constants import folder
app = Flask(__name__)


@app.route('/getqna/<asin>', methods=['GET'])
def getqna(asin):
    try:
        scraper = scrapper.Scraper(asin)
        scraper.scrape_qna()
        return send_from_directory(folder, filename=asin+'.json', as_attachment=True)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run()
