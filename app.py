from flask import Flask, render_template, jsonify
from owl import OWLModel
import helper

app = Flask(__name__)


class JSONError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = self.status_code
        return rv


@app.errorhandler(JSONError)
def handle_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/error')
def test():
    raise JSONError('This is the /error endpoint.', status_code=200)


@app.route('/', methods=['GET'])
def index():
    # try:
    #     model = OWLModel('tests/onts/gnaf-ont.ttl', 'turtle')
    # except Exception as e:
    #     raise JSONError(e.__str__())

    model = OWLModel('tests/onts/gnaf-ont.ttl', 'turtle')

    return render_template('ontology.html', h=helper, ont=model)


@app.context_processor
def context_processor():
    """
    A set of global variables available to 'globally' for jinja templates.

    :return: A dictionary of variables
    :rtype: dict
    """
    return dict(t=helper)


if __name__ == '__main__':
    app.run()