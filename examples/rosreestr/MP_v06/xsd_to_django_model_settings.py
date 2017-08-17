from collections import OrderedDict


RE_NEIGHBOURS = (
    r'(tExistParcel\.|tNewParcel\.|tSpecifyParcel\.(ExistParcel|ExistEZ_ExistEZParcels)_)'
    r'RelatedParcels_ParcelNeighbours'
)

TYPE_MODEL_MAP = OrderedDict([
    (RE_NEIGHBOURS, r'+Neighbours'),
    (RE_NEIGHBOURS + r'\.ParcelNeighbour', r'+Neighbour'),
    (RE_NEIGHBOURS + r'\.ParcelNeighbour\.OwnerNeighbours', r'+NeighbourOwners'),
    (RE_NEIGHBOURS + r'\.ParcelNeighbour\.OwnerNeighbours_OwnerNeighbour', r'+NeighbourOwner'),
    (r'tChangeParcel\.TransformationContours_TransformationContour',
        r'ChangeParcelTransformationContour'),
    (r'tClientIdentify\.Person', r'ClientPerson'),
    (r'tClientIdentify\.ForeignOrganization', r'ClientForeignOrg'),
    (r'tEntitySpatialBordersZUInp\.Borders_Border', r'EntitySpatialBordersZUInpBorder'),
    (r'tEntitySpatialOldNew\.Borders_Border', r'EntitySpatialOldNewBorder'),
    (r'tInvariableSubParcel\.Contours_Contour', r'InvariableSubParcelContour'),
    (r'tSpecifyParcel\.ExistEZ_ExistEZParcels_CompositionEZ_InsertEntryParcels_InsertEntryParcel',
        r'InsertEntryParcel'),
    (r'tSpecifyRelatedParcel\.ExistSubParcels_ExistSubParcel',
        r'SpecifyRelatedParcelExistSubParcel'),
    (r'tSpecifyRelatedParcel\.ExistSubParcels_ExistSubParcel\.Contours_Contour',
        r'SpecifyRelatedParcelExistSubParcelContour'),
    (r'tSubParcel\.Contours_Contour', r'SubParcelContour'),
    (r'typename1', r'LandSurveyPlan'),
    (r'typename1\.Appendix_AppliedFiles', r'LandSurveyPlanAppendixFile'),
    (r'typename1\.InputData_Documents_Document', r'LandSurveyInputDocument'),
    (r'typename1\.InputData_MeansSurvey_MeanSurvey', r'LandSurveyInputMean'),
    (r'typename1\.InputData_ObjectsRealty_ObjectRealty', r'LandSurveyInputObjectRealty'),
    (r'typename1\.InputData_SubParcels_SubParcel', r'LandSurveyInputSubParcel'),
    (r'typename1\.NodalPointSchemes_NodalPointScheme', r'NodalPointScheme'),
    (r'typename1\.Package_SpecifyParcel', r'LandSurveySpecifyParcel'),
    (r'typename1\.Survey_GeopointsOpred_GeopointOpred', r'SurveyGeopointOpred'),
    (r'typename1\.Survey_TochnAreaParcels_TochnAreaParcel', r'SurveyTochnAreaParcel'),
    (r'typename1\.Survey_TochnAreaSubParcels_TochnAreaSubParcel', r'SurveyTochnAreaSubParcel'),
    (r't([A-Z]\w+)', r'\1'),
])

GLOBAL_MODEL_OPTIONS = {
    'one_to_many_fields': ['Documents'],
}

MODEL_OPTIONS = {
    'AddressInp': {
        'abstract': True,
    },
    'AddressInpFull': {
        'abstract': True,
    },
    'AddressInpFullExt': {
        'abstract': True,
    },
    'BordersInp': {
        'one_to_many_fields': ['Border'],
    },
    'CadastralEngineer': {
        'abstract': True,
    },
    'ChangeParcel': {
        'array_fields': ['ObjectRealty_InnerCadastralNumbers'],
        'flatten_fields': ['ObjectRealty', 'SubParcels'],
        'one_to_many_fields': [
            'DeleteEntryParcels',
            'ObjectRealty_OldNumbers',
            'SubParcels_ExistSubParcel',
            'SubParcels_InvariableSubParcel',
            'SubParcels_NewSubParcel',
            'TransformationContours',
            'TransformationEntryParcels',
        ],
    },
    'Encumbrance': {
        'one_to_many_fields': ['Documents'],
    },
    'EntitySpatialBordersZUInp': {
        'one_to_many_fields': ['Borders'],
    },
    'EntitySpatialOldNew': {
        'one_to_many_fields': ['Borders', 'SpatialElement'],
    },
    'EntitySpatialZUInp': {
        'one_to_many_fields': ['SpatialElement'],
    },
    'ExistParcel': {
        'one_to_many_fields': ['Contours', 'RelatedParcels', 'SubParcels'],
    },
    'ExistSubParcel': {
        'one_to_many_fields': ['Contours'],
    },
    'InsertEntryParcel': {
        'array_fields': ['ExistEntryParcel'],
    },
    'InvariableSubParcel': {
        'flatten_fields': ['Area'],
        'one_to_many_fields': ['Contours'],
    },
    'LandSurveyInputDocument': {
        'flatten_fields': ['AdditionalMap'],
    },
    'LandSurveyInputMean': {
        'flatten_fields': ['Registration'],
    },
    'LandSurveyPlan': {
        'flatten_fields': [
            'GeneralCadastralWorks',
            'InputData',
            'Package',
            'Package_FormParcels',
            'Package_SubParcels',
            'Survey',
        ],
        'one_to_many_fields': [
            'Appendix',
            'CoordSystems',
            'GeneralCadastralWorks_Clients',
            'InputData_Documents',
            'InputData_GeodesicBases',
            'InputData_MeansSurvey',
            'InputData_ObjectsRealty',
            'InputData_SubParcels',
            'NodalPointSchemes',
            'Package_FormParcels_ChangeParcel',
            'Package_FormParcels_NewParcel',
            'Package_FormParcels_SpecifyRelatedParcel',
            'Package_FormParcels_SpecifyParcelApproximal',
            'Package_SpecifyParcelsApproximal',
            'Package_SubParcels_ExistSubParcel',
            'Package_SubParcels_NewSubParcel',
            'Survey_GeopointsOpred',
            'Survey_TochnAreaParcels',
            'Survey_TochnAreaSubParcels',
            'Survey_TochnGeopointsParcels',
            'Survey_TochnGeopointsSubParcels',
        ],
    },
    'LandSurveySpecifyParcel': {
        'one_to_many_fields': [
            'SpecifyParcelApproximal',
            'SpecifyRelatedParcel',
        ],
    },
    'Neighbour': {
        'flatten_fields': ['OwnerNeighbours'],
        'one_to_many_fields': [
            'OwnerNeighbours_OwnerNeighbour',
        ],
    },
    'NeighbourOwner': {
        'one_to_many_fields': ['Documents'],
    },
    'Neighbours': {
        'one_to_many_fields': ['ParcelNeighbour'],
    },
    'NewParcel': {
        'flatten_fields': ['Address', 'MinArea', 'MaxArea'],
        'one_to_many_fields': ['Contours', 'RelatedParcels', 'SubParcels'],
    },
    'ObjectRealty': {
        'array_fields': ['InnerCadastralNumbers'],
        'one_to_many_fields': ['OldNumbers'],
    },
    'OrdinateInp': {
        'abstract': True,
    },
    'ProvidingPassCadastralNumbers': {
        'array_fields': ['CadastralNumber', 'Definition'],
        'one_to_many_fields': ['Documents'],
    },
    'SpatialElementOldNew': {
        'one_to_many_fields': ['SpelementUnit'],
    },
    'SpatialElementZUInp': {
        'one_to_many_fields': ['SpelementUnit'],
    },
    'SpecifyParcel': {
        'array_fields': [
            'ExistEZ_ExistEZParcels_CompositionEZ_TransformationEntryParcels',
        ],
        'flatten_fields': [
            'ExistEZ',
            'ExistEZ_ExistEZParcels',
            'ExistEZ_ExistEZParcels_CompositionEZ',
            'ExistEZ_ExistEZParcels_MinArea',
            'ExistEZ_ExistEZParcels_MaxArea',
            'ExistEZ_ExistEZParcels_SubParcels',
            'ExistEZ_ExistEZParcels_RelatedParcels',
            'ExistParcel',
            'ExistParcel_MinArea',
            'ExistParcel_MaxArea',
            'ExistParcel_SubParcels',
            'RelatedParcels',
        ],
        'one_to_many_fields': [
            'ExistEZ_ExistEZEntryParcels',
            'ExistEZ_ExistEZParcels_CompositionEZ_InsertEntryParcels',
            'ExistEZ_ExistEZParcels_CompositionEZ_DeleteEntryParcels',
            'ExistEZ_ExistEZParcels_RelatedParcels',
            'ExistEZ_ExistEZParcels_SubParcels_ExistSubParcel',
            'ExistEZ_ExistEZParcels_SubParcels_InvariableSubParcel',
            'ExistEZ_ExistEZParcels_SubParcels_NewSubParcel',
            'ExistParcel_Contours',
            'ExistParcel_RelatedParcels',
            'ExistParcel_SubParcels_ExistSubParcel',
            'ExistParcel_SubParcels_InvariableSubParcel',
            'ExistParcel_SubParcels_NewSubParcel',
        ],
    },
    'SpecifyRelatedParcel': {
        'flatten_fields': ['AllBorder'],
        'one_to_many_fields': ['ChangeBorder', 'Contours', 'DeleteAllBorder', 'ExistSubParcels'],
    },
    'SpecifyRelatedParcelExistSubParcel': {
        'one_to_many_fields': ['Contours'],
    },
    'SpelementUnitChangeBorder': {
        'flatten_fields': ['NewOrdinate', 'OldOrdinate'],
    },
    'SpelementUnitOldNew': {
        'flatten_fields': ['NewOrdinate', 'OldOrdinate'],
    },
    'SpelementUnitZUInp': {
        'flatten_fields': ['Ordinate'],
    },
    'SubParcel': {
        'one_to_many_fields': ['Contours'],
    },
    'SurveyGeopointOpred': {
        'array_fields': ['Methods'],
    },
    'SurveyTochnAreaParcel': {
        'flatten_fields': ['Area'],
    },
    'SurveyTochnAreaSubParcel': {
        'flatten_fields': ['Area'],
    },
}

TYPE_OVERRIDES = {
    'xs:ID': ('xs:ID identifier', 'CharField', {}),
    'xs:IDREF': ('Reference to an xs:ID identifier', 'CharField', {}),
}
