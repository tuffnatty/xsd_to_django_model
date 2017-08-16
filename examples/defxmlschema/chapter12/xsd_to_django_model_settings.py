TYPE_MODEL_MAP = {
    r'(\w+)Type': r'\1',
}

MODEL_OPTIONS = {
    'Product': {
        'coalesce_fields': {
            r'(color)_value': r'\1',
        },
        'flatten_fields': ['size', 'color'],
    },
}

TYPE_OVERRIDES = {
    'DescriptionType': ('Description in XML format', 'TextField', {}),
}
