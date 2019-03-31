import rdflib
from rdflib.namespace import RDF, RDFS, OWL, SKOS, DC, DCTERMS, URIRef
from rdflib.term import BNode
import owlrl
import pprint as pp

import helper


class OWLProperty:

    def __init__(self, iri, property_name, properties):
        self.iri = iri
        self.property_name = property_name
        self.properties = properties


class Property:
    def __getitem__(self, item):
        """Enable dot operator to access class attributes."""
        return self.__dict__[item]

    @staticmethod
    def get_label(uri, g):
        for o in g.objects(uri, SKOS.prefLabel):
            return o
        for o in g.objects(uri, RDFS.label):
            return o
        return Property._get_label_from_uri(uri)

    @staticmethod
    def _get_label_from_uri(uri):
        """A naive solution to getting a human-readable label from a URI."""
        return uri.split('#')[-1].split('/')[-1]


class OWLClass(Property):
    def __init__(self, uri, g):
        self.uri = str(uri)
        self.label = self.get_label(uri, g)
        self.is_defined_by = self._get_is_defined_by(uri, g)
        self.comment = self._get_comment(uri, g)
        self.sub_class_of = self._get_sub_class_of(uri, g)

    @staticmethod
    def _get_sub_class_of(uri, g):
        super_classes = []

        # Get subject's rdfs:subClassOf the URI and its label (if available)
        # TODO: Get the owl:someValuesFrom property value if available.
        result = g.query("""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX owl: <http://www.w3.org/2002/07/owl#>
                        SELECT ?label ?uri
                        WHERE {{
                            {{
                                <{0}> rdfs:subClassOf ?_blank .
                                ?_blank owl:onProperty ?uri .
                                OPTIONAL {{
                                    ?uri rdfs:label ?label
                                }}
                            }}
                            UNION 
                            {{
                                <{0}> rdfs:subClassOf ?uri .
                                OPTIONAL {{
                                    ?uri rdfs:label ?label .
                                }}
                            }}
                        }}""".format(uri))

        for row in result:
            if not isinstance(row['uri'], BNode):
                label = row['label']
                super_classes.append({
                    'label': label if label is not None else str(row['uri']).split('#')[-1].split('/')[-1],
                    'uri': row['uri']
                })

        return super_classes

    @staticmethod
    def _get_comment(uri, g):
        for o in g.objects(uri, RDFS.comment):
            return o

    @staticmethod
    def _get_is_defined_by(uri, g):
        for o in g.objects(uri, RDFS.isDefinedBy):
            return o


class OWLAnnotationProperty(Property):

    def __init__(self, uri, g):
        self.uri = str(uri)
        self.label = self.get_label(uri, g)
        self.rdfs_range = self._get_label_from_uri(str(self._get_rdfs_range(uri, g)))

    @staticmethod
    def _get_rdfs_range(uri, g):
        for o in g.objects(uri, RDFS.range):
            return o


class OWLModel:

    # Namespace prefix mappings
    _namespaces = [
        (rdflib.namespace.RDF, 'rdf'),
        (rdflib.namespace.RDFS, 'rdfs'),
        (rdflib.namespace.OWL, 'owl'),
        (rdflib.namespace.XSD, 'xsd'),
        (rdflib.namespace.FOAF, 'foaf'),
        (rdflib.namespace.SKOS, 'skos'),
        (rdflib.namespace.DOAP, 'doap'),
        (rdflib.namespace.DC, 'dc'),
        (rdflib.namespace.DCTERMS, 'dct'),
        (rdflib.namespace.VOID, 'void'),
    ]

    def __init__(self, source, format):

        g = rdflib.Graph()
        g.parse(source, format=format)

        # Testing ... TODO: For each OWL property, I need to
        # results = []
        # results = g.query("""
        #     PREFIX owl: <http://www.w3.org/2002/07/owl#>
        #     PREFIX prov: <http://www.w3.org/ns/prov#>
        #     PREFIX : <http://gnafld.net/def/gnaf#>
        #     SELECT *
        #     WHERE {{
        #         :hasDateCreated owl:sameAs ?value
        #     }}
        #     """)
        # for row in results:
        #     print(row['value'])

        # the turtle file only states that gnaf:hasDateCreated owl:sameAs prov:wasGeneratedAtTime
        # and with owlrl, we're able to infer the inverse is also the same
        # result: prov:wasGeneratedAtTime owl:sameAs gnaf:hasDateCreated
        # owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
        # results = g.query("""
        #             PREFIX owl: <http://www.w3.org/2002/07/owl#>
        #             PREFIX prov: <http://www.w3.org/ns/prov#>
        #             PREFIX : <http://gnafld.net/def/gnaf#>
        #             SELECT *
        #             WHERE {{
        #                 prov:wasGeneratedAtTime owl:sameAs ?value
        #             }}
        #             """)
        # for row in results:
        #     print(row['value'])

        # results = []
        # # owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
        # results = g.query("""
        #     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #     PREFIX : <http://gnafld.net/def/gnaf#>
        #     SELECT *
        #     WHERE {{
        #         :MB2011 rdfs:subClassOf ?comment .
        #     }}
        #     """)
        # for row in results:
        #     print(row['comment'])

        self.iri = OWLModel._get_IRI(g)
        if not self.iri:
            raise Exception('Failed to find the IRI by matching (?iri rdf:type owl:Ontology) in {}'.format(source))

        self.title = OWLModel._get_title(g, self.iri)
        self.version_IRI = OWLModel._get_version_IRI(g, self.iri)
        self.version = OWLModel._get_version(g, self.iri)
        self.authors = OWLModel._get_authors(g, self.iri)
        self.contributors = OWLModel._get_contributors(g, self.iri)
        self.publishers = OWLModel._get_publishers(g, self.iri)
        self.imported_ontologies = OWLModel._get_imported_ontologies(g, self.iri)
        self.sources = OWLModel._get_sources(g, self.iri)
        self.comment = OWLModel._get_comment(g, self.iri)

        self.annotation_properties = OWLModel._get_annotation_properties(g)
        self.classes = OWLModel._get_classes(g)

        # self.named_individuals = OWLModel._get_object_type_properties(g, OWL.NamedIndividual)
        # self.data_properties = OWLModel._get_object_type_properties(g, OWL.DatatypeProperty)
        # self.object_properties = OWLModel._get_object_type_properties(g, OWL.ObjectProperty)
        # self.classes = OWLModel._get_object_type_properties(g, OWL.Class)

        self.namespaces = OWLModel._get_namespaces(g, self.iri)

    @staticmethod
    def _get_classes(g):
        classes = []
        for s in g.subjects(RDF.type, OWL.Class):
            classes.append(OWLClass(s, g))
        classes.sort(key=OWLModel._sort_obj_props_key)
        return classes

    @staticmethod
    def _get_annotation_properties(g):
        annotation_properties = []
        for s in g.subjects(RDF.type, OWL.AnnotationProperty):
            annotation_properties.append(OWLAnnotationProperty(s, g))
        annotation_properties.sort(key=OWLModel._sort_obj_props_key)
        return annotation_properties

    def get_default_namespace(self):
        return self.iri + '#'

    @staticmethod
    def _get_namespaces(g, IRI):
        IRI = IRI + '#'
        namespaces = []
        uris = set(g.subjects()).union(g.predicates()).union(g.objects())
        for uri in uris:
            if isinstance(uri, rdflib.URIRef):
                property_name = uri.split('#')[-1].split('/')[-1]
                uri = uri[:len(uri)-len(property_name)]
                if uri not in namespaces:
                    # Don't add the URI if it gets trimmed to 'http://' or if it is the default namespace
                    if uri != 'http://' and uri != str(IRI):
                        # if in OWLModel._namespaces, use it
                        for n in OWLModel._namespaces:
                            if str(n[0]) == uri:
                                if (str(n[0])) not in [x[0] for x in namespaces]:
                                    namespaces.append((str(n[0]), n[1]))
                                    continue  # go to the next loop
                        # else find the label using string splits
                        namespace_name = uri[:-1].split('/')[-1]
                        if uri not in [x[0] for x in namespaces]:
                            namespaces.append((uri, namespace_name))
        namespaces.sort(key=OWLModel._sort_namespaces_key)
        return namespaces

    @staticmethod
    def _sort_namespaces_key(elem):
        """


        :param elem:
        :return:
        """
        return elem[1]

    @staticmethod
    def _sort_obj_props_key(elem):
        """
        This is the key for a sort function. Sort the OWL property by its label.

        :param elem: An element of an RDF property list.
        :return: label
        :rtype: str
        """
        return elem.label.lower()

    @staticmethod
    def _get_object_type_properties(g, object_type):
        object_type_properties = [] # like AnnotationProperties, NamedIndividuals, etc.
        ss = [] # list of subjects
        # print('START OF NEW')
        # find all the subjects and append to list ss
        for s, p, o in g.triples((None, RDF.type, object_type)):
            ss.append(s)
        print('')
        for s_ in ss:
            ps = [] # list of predicates
            for s, p, o in g.triples((s_, None, None)):
                if p not in ps: # find all unique predicates and add to list ps
                    ps.append(p)

            properties = [] # properties of the object_type
            label = None
            for p_ in ps:
                for s, p, o in g.triples( (s_, p_, None) ):
                    properties.append( (p, o) )

            if not label:
                for s, p, o in g.triples( (s_, RDFS.label, None) ):
                    if o is not None:
                        label = o.value
                        break
            # TODO: refactor this so that it extracts each property of the OWL property to its individual variables to be displayed in jinja.
            label = helper.extract_property_name_from_uri(s, label=label)
            class_type_property = OWLProperty(s, label, properties)
            object_type_properties.append(class_type_property)
        object_type_properties.sort(key=OWLModel._sort_obj_props_key)
        return object_type_properties

    @staticmethod
    def _get_comment(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), RDFS.comment, None)):
            return o

    @staticmethod
    def _get_sources(g, IRI):
        sources = []
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.source, None)):
            sources.append(o)
        return sources

    @staticmethod
    def _get_imported_ontologies(g, IRI):
        imported_ontologies = []
        for s, p, o in g.triples((URIRef(IRI), OWL.imports, None)):
            imported_ontologies.append(o)
        imported_ontologies.sort()
        return imported_ontologies

    @staticmethod
    def _get_publishers(g, IRI):
        publishers = []
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.publisher, None)):
            publishers.append(o)
        for s, p, o in g.triples((URIRef(IRI), DC.publisher, None)):
            publishers.append(o)
        publishers.sort()
        return publishers

    @staticmethod
    def _get_contributors(g, IRI):
        contributors = []
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.contributor, None)):
            contributors.append(o)
        for s, p, o in g.triples((URIRef(IRI), DC.contributor, None)):
            contributors.append(o)
        contributors.sort()
        return contributors

    @staticmethod
    def _get_authors(g, IRI):
        authors = []
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.creator, None)):
            authors.append(o)
        for s, p, o in g.triples( (URIRef(IRI), DC.creator, None) ):
            authors.append(o)
        authors.sort()
        return authors

    @staticmethod
    def _get_version(g, IRI):
        for s, p, o in g.triples( (URIRef(IRI), OWL.versionInfo, None) ):
            return o

    @staticmethod
    def _get_version_IRI(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), OWL.versionIRI, None)):
            return o

    @staticmethod
    def _get_title(g, IRI):
        for s, p, o in g.triples((URIRef(IRI), DCTERMS.title, None)):
            return o
        for s, p, o in g.triples((URIRef(IRI), DC.title, None)):
            return o
        for s, p, o in g.triples((URIRef(IRI), SKOS.prefLabel, None)):
            return o
        for s, p, o in g.triples( ( URIRef(IRI), RDFS.label, None) ):
            return o

    @staticmethod
    def _get_IRI(g):
        for s, p, o in g.triples( (None, RDF.type, OWL.Ontology) ):
            return s
