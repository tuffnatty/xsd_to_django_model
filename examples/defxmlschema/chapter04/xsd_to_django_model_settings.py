TYPE_MODEL_MAP = {
    r'prod:(.+)Type': r'\1',
    r'(\w+)Type': r'\1',
}

MODEL_OPTIONS = {
    'Product': {
        'flatten_fields': ['color', 'size']
    },
}
