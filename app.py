import rdflib
from rdflib.namespace import RDF, RDFS, OWL, SKOS, DC, DCTERMS, URIRef
import pprint as pp


class RDFClass:

    def __init__(self):
        pass


class RDFAnnotationProperty:

    def __init__(self, IRI, property_name):
        self.IRI = IRI
        self.property_name = property_name


class RDFModel:

    def __init__(self, source, format):
        g = rdflib.Graph()
        g.parse(source, format=format)

        self.get_ontology_properties(g)
        self.get_annotation_properties(g)

    def get_annotation_properties(self, g):
        self.annotation_properties = []

        for s, p, o in g.triples( (None, RDF.type, OWL.AnnotationProperty) ):
            property_name = str(s) # cast to str
            # split on '#' if it exists, then on '/' and grab the last token
            property_name = property_name.split('#')[-1].split('/')[-1]

            # split the property_name if it is in camelCase or PascalCase
            for i, letter in enumerate(property_name):
                if letter.isupper():
                    property_name = property_name[:i] + ' ' + property_name[i:]
                    property_name = property_name.lower()

            ap = RDFAnnotationProperty(s, property_name)
            self.annotation_properties.append(ap)
            # print(f'IRI: {s} property_name: {property_name}')

    def get_ontology_properties(self, g):
        self.IRI = RDFModel.get_IRI(g)
        # print(self.IRI)

        self.title = RDFModel.get_title(g, self.IRI)
        # print(self.title)

        self.version_IRI = RDFModel.get_version_IRI(g, self.IRI)
        # print(self.version_IRI)

        self.version = RDFModel.get_version(g, self.IRI)
        # print(self.version)

        self.authors = RDFModel.get_authors(g, self.IRI)
        # print(self.authors)

        self.contributors = RDFModel.get_contributors(g, self.IRI)
        # print(self.contributors)

        self.publisher = RDFModel.get_publisher(g, self.IRI)
        # print(self.publisher)

        self.imported_ontologies = RDFModel.get_imported_ontologies(g, self.IRI)
        # print(self.imported_ontologies)

        self.source = RDFModel.get_source(g, self.IRI)
        # print(self.source)

        self.comment = RDFModel.get_comment(g, self.IRI)
        # print(self.comment)

    @staticmethod
    def get_comment(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), RDFS.comment, None)):
            if o is not None:
                return o

    @staticmethod
    def get_source(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.source, None)):
            if o is not None:
                return o

    @staticmethod
    def get_imported_ontologies(g, IRI):
        imported_ontologies = []
        for s, p, o in g.triples((URIRef(IRI), OWL.imports, None)):
            if o is not None:
                imported_ontologies.append(str(o))
        return imported_ontologies

    @staticmethod
    def get_publisher(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.publisher, None)):
            if o is not None:
                return o

    @staticmethod
    def get_contributors(g, IRI):
        contributors = []
        for s, p, o in g.triples((URIRef(IRI), DC.contributor, None)):
            if o is not None:
                contributors.append(o.value)
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.contributor, None)):
            if o is not None:
                contributors.append(str(o))
        return contributors

    @staticmethod
    def get_authors(g, IRI):
        authors = []
        for s, p, o in g.triples( (URIRef(IRI), DC.creator, None) ):
            if o is not None:
                authors.append(o.value)
        for s, p, o in g.triples( (URIRef(IRI), DCTERMS.creator, None) ):
            if o is not None:
                authors.append(str(o))
        return authors

    @staticmethod
    def get_version(g, IRI):
        for s, p, o in g.triples( (URIRef(IRI), OWL.versionInfo, None) ):
            if o is not None:
                return o

    @staticmethod
    def get_version_IRI(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), OWL.versionIRI, None)):
            if o is not None:
                return o

    @staticmethod
    def get_title(g, IRI):
        for s, p, o in g.triples( ( URIRef(IRI), RDFS.label, None) ):
            if o is not None:
                return o
        for s, p, o in g.triples( ( URIRef(IRI), SKOS.prefLabel, None) ):
            if o is not None:
                return o
        for s, p, o in g.triples( ( URIRef(IRI), DC.title, None) ):
            if o is not None:
                return o
        for s, p, o in g.triples( ( URIRef(IRI), DCTERMS.title, None) ):
            if o is not None:
                return o

    @staticmethod
    def get_IRI(g):
        for s, p, o in g.triples( (None, RDF.type, OWL.Ontology) ):
            if s is not None:
                return s


model = RDFModel('tests/onts/gnaf-ont.ttl', 'text/turtle')

