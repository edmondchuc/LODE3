from flask import Flask, render_template
from rdf_objects import RDFModel
import toolkit

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    model = RDFModel('tests/onts/gnaf-ont.ttl', 'text/turtle')

    # from markdown2 import Markdown
    # markdowner = Markdown()
    # print(markdowner.convert(model.comment))

    return render_template('ontology.html', t=toolkit, ont=model)


if __name__ == '__main__':
    app.run()