TYPE_MODEL_MAP = {
    r'(\w+)Type': r'\1',
}

MODEL_OPTIONS = {
    'Shirt': {
        'flatten_fields': ['color', 'size'],
    },
}

TYPE_OVERRIDES = {
    'xs:language': ('RFC1766 language code', 'CharField', {'max_length': 3}),
}
