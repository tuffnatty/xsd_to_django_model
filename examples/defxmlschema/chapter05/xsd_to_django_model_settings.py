TYPE_MODEL_MAP = {
    r'prod:(.+)Type': r'\1',
    r'(\w+)Type': r'\1',
}

MODEL_OPTIONS = {
    'Order': {
        'many_to_many_fields': ['items'],
    },
    'Product': {
        'flatten_fields': ['size'],
        'primary_key': 'number',
    }
}
