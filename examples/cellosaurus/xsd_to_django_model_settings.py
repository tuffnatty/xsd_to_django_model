TYPE_MODEL_MAP = {
    'typename1': 'Cellosaurus',
    'typename1.header_terminologyList_terminology': 'Terminology',
    'typename1.cellLineList_cell-line': 'CellLine',
    'typename1.cellLineList_cell-line.accessionList_accession': 'CellLineAccession',
    'typename1.cellLineList_cell-line.commentList_comment': 'Comment',
    'typename1.cellLineList_cell-line.commentList_comment.xrefList_xref': 'CommentXref',
    'typename1.cellLineList_cell-line.commentList_comment.xrefList_xref.propertyList_property': 'CommentXrefProperty',
    'typename1.cellLineList_cell-line.derivedFrom_cvTerm': 'DerivedFrom',
    'typename1.cellLineList_cell-line.derivedFromSiteList_derived-from-site': 'DerivedFromSite',
    'typename1.cellLineList_cell-line.derivedFromSiteList_derived-from-site.site': 'Site',
    'typename1.cellLineList_cell-line.derivedFromSiteList_derived-from-site.site.cvTerm': 'SiteCvTerm',
    'typename1.cellLineList_cell-line.diseaseList_cvTerm': 'Disease',
    'typename1.cellLineList_cell-line.doublingTimeList_doubling-time': 'DoublingTime',
    'typename1.cellLineList_cell-line.doublingTimeList_doubling-time.doublingTimeSources_xrefList_xref': 'DoublingTimeSourceXref',
    'typename1.cellLineList_cell-line.doublingTimeList_doubling-time.doublingTimeSources_xrefList_xref.propertyList_property': 'DoublingTimeSourceXrefProperty',
    'typename1.cellLineList_cell-line.genomeAncestry_populationList_population': 'GenomeAncestryPopulation',
    'typename1.cellLineList_cell-line.hlaTypingList_hla-typing': 'HlaTyping',
    'typename1.cellLineList_cell-line.hlaTypingList_hla-typing.hlaGeneAllelesList_hlaGeneAlleles': 'HlaTypingGeneAlleles',
    'typename1.cellLineList_cell-line.hlaTypingList_hla-typing.hlaTypingSource_xref_propertyList_property': 'HlaTypingSourceXrefProperty',
    'typename1.cellLineList_cell-line.misspellingList_misspelling': 'Misspelling',
    'typename1.cellLineList_cell-line.misspellingList_misspelling.xrefList_xref': 'MisspellingXref',
    'typename1.cellLineList_cell-line.misspellingList_misspelling.xrefList_xref.propertyList_property': 'MisspellingXrefProperty',
    'typename1.cellLineList_cell-line.nameList_name': 'CellLineName',
    'typename1.cellLineList_cell-line.registrationList_registration': 'Registration',
    'typename1.cellLineList_cell-line.sameOriginAs_cvTerm': 'SameOriginAs',
    'typename1.cellLineList_cell-line.sequenceVariationList_sequence-variation': 'SequenceVariation',
    'typename1.cellLineList_cell-line.sequenceVariationList_sequence-variation.variationSources': 'SequenceVariationSource',
    'typename1.cellLineList_cell-line.sequenceVariationList_sequence-variation.xrefList_xref': 'SequenceVariationXref',
    'typename1.cellLineList_cell-line.sequenceVariationList_sequence-variation.xrefList_xref.propertyList_property': 'SequenceVariationXrefProperty',
    'typename1.cellLineList_cell-line.speciesList_cvTerm': 'Species',
    'typename1.cellLineList_cell-line.strList_markerList_marker': 'StrMarker',
    'typename1.cellLineList_cell-line.strList_markerList_marker.markerDataList_markerData': 'StrMarkerData',
    'typename1.cellLineList_cell-line.xrefList_xref': 'CellLineXref',
    'typename1.cellLineList_cell-line.xrefList_xref.propertyList.property': 'CellLineXrefProperty',
    'typename1.publicationList_publication': 'Publication',
    'typename1.publicationList_publication.authorList_consortium': 'AuthorConsortium',
    'typename1.publicationList_publication.authorList_person': 'AuthorPerson',
    'typename1.publicationList_publication.editorList_consortium': 'EditorConsortium',
    'typename1.publicationList_publication.editorList_person': 'EditorPerson',
    'typename1.publicationList_publication.xrefList_xref': 'PublicationXref',
    'typename1.publicationList_publication.xrefList_xref.propertyList.property': 'PublicationXrefProperty',
}

GLOBAL_MODEL_OPTIONS = {
    'flatten_fields': [
        'nameList',
        'propertyList',
        'referenceList',
        'xrefList',
    ],
    'level1_substitutions': {
        # Convert barbecue-case to camelCase
        r'(.*-.*)': lambda m: ''.join(part.capitalize() if n > 0 else part
                                      for n, part in enumerate(m.group(1).split("-"))),
        # id column name is only allowed as the primary key
        r'id': 'cellosaurus_id',
    },
    'one_to_many_fields': [
        'nameList_name',
        'propertyList_property',
        'xrefList_xref',
    ],
    'strategy': 1,
}

MODEL_OPTIONS = {
    'Cellosaurus': {
        'field_options': {
            'header_release_version': [
                # A DecimalField must have max_digits and decimal_places.
                # FIXME: this is a wild guess on the actual values.
                'max_digits=10',
                'decimal_places=5',
            ],
        },
        'one_to_many_fields': [
            'publicationList',
        ],
    },

    'CellLine': {
        'array_fields': [
            'referenceList_reference',
            'strList_sourceList_referenceList_reference',
            'webPageList',
        ],
        'flatten_fields': [
            'accessionList',
            'commentList',
            'derivedFrom',
            'diseaseList',
            'genomeAncestry_populationList',
            'registrationList',
            'sameOriginAs',
            'speciesList',
            'strList_sourceList_referenceList',
        ],
        'level3_substitutions': {
            # Prevent column names longer than 63 chars
            r'genomeAncestry_genomeAncestrySource_(reference_resourceInternalRef|source)':
                r'genomeAncestry_source_\1',
        },
        'one_to_many_fields': [
            'accessionList_accession',
            'derivedFrom_cvTerm',
            'diseaseList_cvTerm',
            'speciesList_cvTerm',
            'strList_markerList',
        ],
    },

    'CellLineXref': {
    },

    'CommentXref': {
    },

    'DerivedFrom': {
        'level3_substitutions': {
            # For some reason level1_substitutions are not enough here:
            'cv-term': 'cvTerm',
        },
    },

    'DoublingTime': {
        'array_fields': [
            'doublingTimeSources_referenceList_reference',
            'doublingTimeSources_sourceList_referenceList_reference',
        ],
        'flatten_fields': [
            'doublingTimeSources_xrefList',
            'doublingTimeSources_referenceList',
            'doublingTimeSources_sourceList_referenceList',
        ],
    },

    'HlaTyping': {
        'flatten_fields': [
            'hlaGeneAllelesList',
            'hlaTypingSource_xref_propertyList',
        ],
    },

    'Misspelling': {
        'array_fields': [
            'referenceList_reference',
        ],
    },

    'Publication': {
        'one_to_many_fields': [
            'authorList_consortium',
            'authorList_person',
            'editorList_consortium',
            'editorList_person',
            'xrefList_xref',
        ],
    },

    'PublicationXref': {
    },

    'SequenceVariationSource': {
        'array_fields': [
            'referenceList_reference',
        ],
    },

    'StrMarker': {
        'flatten_fields': [
            'markerDataList',
        ],
    },

    'StrMarkerData': {
        'array_fields': [
            'sourceList_referenceList_reference',
        ],
        'flatten_fields': [
            'sourceList_referenceList',
        ],
    },

}
