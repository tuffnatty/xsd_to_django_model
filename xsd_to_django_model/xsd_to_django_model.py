#! /usr/bin/env python

"""
xsd_to_django_model
Generate Django models from an XSD schema description (and a bunch of hints).

Usage:
    xsd_to_django_model.py [-m <models_filename>] [-f <fields_filename>]
                           [-j <mapping_filename>] <xsd_filename> <xsd_type>...
    xsd_to_django_model.py -h | --help

Options:
    -h --help              Show this screen.
    -m <models_filename>   Output models filename [default: models.py].
    -f <fields_filename>   Output fields filename to generate custom fields.
    -j <mapping_filename>  Output JSON mapping filename
                           [default: mapping.json].
    <xsd_filename>         Input XSD schema filename.
    <xsd_type>             XSD type (or an XPath query for XSD type) for which
                           a Django model should be generated.

If you have xsd_to_django_model_settings.py in your PYTHONPATH or in the
current directory, it will be imported.
"""


import codecs
from copy import deepcopy
import datetime
import decimal
from functools import partial, wraps
from itertools import chain, groupby
import json
import logging
from operator import itemgetter
import pickle
import re
import sys
import textwrap

from docopt import docopt
import ndifflib
import xmlschema


try:
    from xsd_to_django_model_settings import TYPE_MODEL_MAP
except ImportError:
    TYPE_MODEL_MAP = {}
try:
    from xsd_to_django_model_settings import MODEL_OPTIONS
except ImportError:
    MODEL_OPTIONS = {}
try:
    from xsd_to_django_model_settings import GLOBAL_MODEL_OPTIONS
except ImportError:
    GLOBAL_MODEL_OPTIONS = {}
try:
    from xsd_to_django_model_settings import TYPE_OVERRIDES
except ImportError:
    TYPE_OVERRIDES = {}
try:
    from xsd_to_django_model_settings import BASETYPE_OVERRIDES
except ImportError:
    BASETYPE_OVERRIDES = {}
try:
    from xsd_to_django_model_settings import IMPORTS
except ImportError:
    IMPORTS = ''
try:
    from xsd_to_django_model_settings import DOC_PREPROCESSOR
except ImportError:
    DOC_PREPROCESSOR = ''
try:
    from xsd_to_django_model_settings import JSON_DOC_HEADING
except ImportError:
    JSON_DOC_HEADING = "JSON attributes:\n"
try:
    from xsd_to_django_model_settings import JSON_GROUP_HEADING
except ImportError:
    JSON_GROUP_HEADING = "*   JSON attribute group \u2013 "
try:
    from xsd_to_django_model_settings import JSON_DOC_INDENT
except ImportError:
    JSON_DOC_INDENT = " " * 4
try:
    from xsd_to_django_model_settings import MAX_LINE_LENGTH
except ImportError:
    MAX_LINE_LENGTH = 80


BASETYPE_FIELD_MAP = {
    'xs:anySimpleType': 'JSONField',
    'xs:base64Binary': 'BinaryField',
    'xs:boolean': 'BooleanField',
    'xs:byte': 'SmallIntegerField',
    'xs:date': 'DateField',
    'xs:dateTime': 'DateTimeField',
    'xs:decimal': 'DecimalField',
    'xs:double': 'FloatField',
    'xs:gYearMonth': 'DateField',  # Really YYYY-MM
    'xs:hexBinary': 'BinaryField',
    'xs:int': 'IntegerField',
    'xs:integer': 'IntegerField',
    'xs:long': 'BigIntegerField',
    'xs:nonNegativeInteger': 'PositiveIntegerField',
    'xs:normalizedString': 'CharField',
    'xs:positiveInteger': 'PositiveIntegerField',
    'xs:short': 'SmallIntegerField',
    'xs:string': 'CharField',
    'xs:token': 'CharField',
    'xs:unsignedInt': 'BigIntegerField',
}

BASETYPE_FIELD_MAP.update(BASETYPE_OVERRIDES)

NS = {'xs': "http://www.w3.org/2001/XMLSchema"}

FIELD_TMPL = {
    '_coalesce':
        '{dotted_name} => {coalesce}',
    'drop':
        '    # Dropping {dotted_name}',
    'parent_field':
        '    # {dotted_name} field translates to this model\'s parent',
    'one_to_many':
        '    # {name} is declared as a reverse relation\n'
        '    #  from {options0}\n'
        '    # {name} = OneToManyField({serialized_options})',
    'one_to_one':
        '    # {name} is declared as a reverse relation\n'
        '    #  from {options0}\n'
        '    # {name} = OneToOneField({serialized_options})',
    'wrap':
        '    {name} = {wrap}({final_django_field}({serialized_options})'
        ', {wrap_options})',
    'default':
        '    {name} = {final_django_field}({serialized_options})',
}

HEADER = ('# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT\n'
          '# -*- coding: utf-8 -*-\n\n'
          'from __future__ import unicode_literals\n\n')

RE_SPACES = re.compile('([^\n])  +', re.U)
RE_KWARG = re.compile(r'^[a-zi0-9_]+=')
RE_CAMELCASE_TO_UNDERSCORE_1 = re.compile(r'(.)([A-Z][a-z]+)')
RE_CAMELCASE_TO_UNDERSCORE_2 = re.compile(r'([a-z0-9])([A-Z])')
RE_RELATED_FIELD = re.compile(r'^models\.(ForeignKey|ManyToManyField)$')
RE_RE_DECIMAL = re.compile(r'\\d\{(|(\d+),)(\d+)\}'
                           r'\(?\\\.\\d\{(|(\d+),)(\d+)\}(\)\?)?')
RE_FIELD_CLASS_FILTER = re.compile(r'[^a-zA-Z0-9_]')
RE_MARKDOWN_LIST_ENTRY = re.compile(r"^([-+ *]|\d+[).]) ")

MAX_OCCURS_UNBOUNDED = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


depth = -1


def memoize(function):
    memo = {}

    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            if rv:
                memo[args] = rv
            return rv
    return wrapper


def cat(seq):
    return tuple(chain.from_iterable(seq))


def info(s):
    sys.stderr.write('%s%s' % (' ' * depth, s))


def xfind(root, path, **kwargs):
    # For simple ElementTree-compatible queries
    return root.findall(path, namespaces=NS, **kwargs)


@memoize
def get_model_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.items():
        if re.match(expr + '$', name):
            return re.sub(expr + '$', sub, name).replace('+', '')
    return None


def schema_get_type(schema, typename):
    ns, name = get_ns(typename), strip_ns(typename)
    return (schema.imports[schema.namespaces[ns]]
            if schema.namespaces[ns] in schema.imports
            else schema).types.get(name)


def get_a_type_for_model(name, schema):
    names = (name, '+%s' % name)
    exprs = (expr for expr, sub in TYPE_MODEL_MAP.items()
             if ('(' not in expr and '\\' not in expr and sub in names))
    typename = None
    for expr in exprs:
        typename = expr
        if isinstance(schema_get_type(schema, typename),
                      xmlschema.validators.XsdComplexType):
            break
    return typename


@memoize
def get_merge_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.items():
        if re.match(expr + '$', name):
            return sub.startswith('+')
    return False


@memoize
def get_opt(model_name, typename=None):
    opt = MODEL_OPTIONS.get(model_name, {})
    if not typename:
        return opt
    for opt2 in (o for pattern, o in opt.get('if_type', {}).items()
                 if re.match(pattern + '$', typename)):
        opt = deepcopy(opt)
        for k, v in opt2.items():
            try:
                v1 = opt[k]
            except KeyError:
                opt[k] = v
            else:
                if type(v1) == dict and type(v) == dict:
                    opt[k] = dict(v1, **v)
                elif isinstance(v1, (str, bytes)) and \
                        isinstance(v, (str, bytes)):
                    opt[k] = v
                elif k == 'add_fields':
                    opt[k] = list(chain(v1, v))
                else:
                    opt[k] = list(set(chain(v1, v)))
    return opt


def get_doc(el_def, name, model_name, doc_prefix=None, choices=None):
    if isinstance(el_def, (xmlschema.validators.XsdType,
                           xmlschema.validators.XsdAttribute,
                           xmlschema.validators.XsdElement)):
        xs_el = el_def
        el_def = xs_el.elem
    else:
        xs_el = None
    name = name or (xs_el.prefixed_name if xs_el else el_def.get('name'))
    if model_name:
        try:
            return get_opt(model_name)['field_docs'][name]
        except KeyError:
            pass
    if xs_el and xs_el.annotation:
        doc = (d.text for d in xs_el.annotation.documentation if d.text)
    else:
        doc = (d.text for d in
               chain(xfind(el_def, "xs:annotation/xs:documentation"),
                     xfind(el_def, "xs:complexType/xs:annotation/xs:documentation"))
               if d.text)
    doc = '\n'.join([RE_SPACES.sub(r'\1 ', d.strip())
                     .replace(' )', ')').replace('\n\n', '\n').replace(' \n', '\n')
                     for d in doc])
    if choices:
        doc = ((doc + ':\n') if doc else '') + '\n'.join(
            '%s%s' % (c[0], ' - %s' % c[1] if c[1] != c[0] else '')
            for c in choices
            if not re.search(r"^%s(| - .*)$" % c[0], doc or "", re.M)
        )
    if DOC_PREPROCESSOR:
        doc = DOC_PREPROCESSOR(doc)
    if doc_prefix:
        return doc_prefix + (doc or name)
    return doc or None


def circled(n):
    return chr(n + (0x2460 if n < 20 else (0x3251 - 20)))


def mark_diff_n(seq, n):
    for containers, lines in seq:
        if len(containers) == n:
            prefix = ''
        else:
            prefix = ''.join(circled(n) + ' ' for n in containers)
        for line in lines:
            yield prefix + line


def makediff_n(sequences):
    if len(sequences) == 1:
        return sequences[0]
    sm = ndifflib.SequenceMatcher(None, *sequences).get_opcodes()
    markup = []
    for opcode, begins, indices in sm:
        if opcode == 'equal':
            containers = list(range(len(begins)))
        else:
            containers = list(n for n in range(len(begins))
                              if indices[n] != begins[n])
        container = containers[0]
        sequence = sequences[container]
        markup.append((containers,
                       sequence[begins[container]:indices[container]]))
    return mark_diff_n(markup, len(sequences))


@memoize
def stringify(s, max_length=None):
    if type(s) is tuple:
        s = sorted(set(el.strip() for el in s))
        s = '\n'.join(makediff_n([el.split('\n') for el in s]))
    s = s \
        .replace('\\', '\\\\') \
        .replace('"', '\\"')
    if max_length:
        return '"%s"' % '\\n"\n"'.join(
            '"\n"'.join(textwrap.wrap(_, width=max_length - 4,
                                      break_long_words=False, drop_whitespace=False))
            for _ in s.split('\n')
        )
    return '"%s"' % s.replace('\n', '\\n"\n"')


def multiline_comment(s, indent=4):
    prefix = " " * indent + "# "
    return "\n".join(textwrap.wrap(s, width=MAX_LINE_LENGTH, break_long_words=False,
                                   initial_indent=prefix,
                                   subsequent_indent=prefix + " ")) + "\n"


def get_null(el_def):
    return el_def.occurs[0] == 0


@memoize
def get_ns(typename):
    if typename and ':' in typename:
        return typename.split(':')[0]
    return ''


def strip_ns(typename):
    if typename and ':' in typename and not typename.startswith("xs:"):
        _, typename = typename.split(':')
    return typename


@memoize
def camelcase_to_underscore(name):
    s1 = RE_CAMELCASE_TO_UNDERSCORE_1.sub(r'\1_\2', name)
    return RE_CAMELCASE_TO_UNDERSCORE_2.sub(r'\1_\2', s1).lower()


def coalesce(name, model, option):
    try:
        expr, sub = next(
            (expr, sub)
            for expr, sub in chain(GLOBAL_MODEL_OPTIONS.get(option, {}).items(),
                                   model.get(option, {}).items())
            if re.match(expr + '$', name)
        )
    except StopIteration:
        return None
    return re.sub(expr + '$', sub, name)


def match(name, model, kind):
    for expr in chain(model.get(kind, ()),
                      GLOBAL_MODEL_OPTIONS.get(kind, ())):
        if re.match(expr + '$', name):
            return True
    return False


def parse_user_options(options):
    return (dict(o.split('=', 1) if RE_KWARG.match(o) else ('_', o)
                 for o in (options or ()))
            if not isinstance(options, dict)
            else options)


def override_field_options(field_name, options, model_options, field_type):
    this_field_add_options = {
        **parse_user_options(GLOBAL_MODEL_OPTIONS.get('field_options', {}).get(field_name, {})),
        **parse_user_options(model_options.get('field_type_options', {}).get(field_type, {})),
        **parse_user_options(model_options.get('field_options', {}).get(field_name, {})),
    }
    options = {k: v for k, v in options.items()
               if k not in this_field_add_options}
    options.update((k, v) for k, v in this_field_add_options.items()
                   if v != 'None')
    return options


@memoize
def override_field_class(model_name, typename, name):
    return get_opt(model_name, typename) \
        .get('override_field_class', {}) \
        .get(name)


@memoize
def parse_default(basetype, default):
    if basetype == "xs:boolean":
        assert default in ("true", "false"), (
            "cannot parse boolean default value: %s" % default
        )
        return (default == "true")
    if basetype == "xs:date":
        return datetime.datetime.strptime(default, "%Y-%m-%d").date()
    if basetype == "xs:dateTime":
        return datetime.datetime.strptime(default, "%Y-%m-%dT%H:%M:%S")
    if basetype == "xs:double":
        return float(default)
    if basetype == "xs:decimal":
        return decimal.Decimal(default)
    if basetype == "xs:gYearMonth":
        return datetime.datetime.strptime(default + "-01", "%Y-%m-%d").date()
    if basetype == "xs:long":
        return int(default)
    if basetype == "xs:string":
        return default
    if basetype == "xs:token":
        return ''.join(default.split())
    if basetype in ("xs:byte", "xs:int", "xs:integer",
                    "xs:nonNegativeInteger", "xs:positiveInteger", "xs:short"):
        return int(default)
    assert False, "parsing default value '%s' for %s type not implemented" \
        % (default, basetype)


def indent_multiline(doc, indent):
    return "\n{indent}{doc}\n".format(doc=doc.replace("\n", "\n" + indent),
                                      indent=indent)


def markdown_to_bullet_list(doc, first=""):
    result = []
    for n, line in enumerate(doc.split('\n')):
        if n == 0:
            prefix = first
        elif RE_MARKDOWN_LIST_ENTRY.match(line):
            prefix = " " * len(first)
        else:
            prefix = first
        if line:
            result.append(prefix + line)
    return '\n'.join(result)


class Model:

    def __init__(self, builder, model_name, type_name):
        self.builder = builder
        self.model_name = model_name
        self.type_name = type_name
        self.fields = []
        self.parent = None
        self.parent_model = None
        self.code = None
        self.deps = None
        self.match_fields = None
        self.written = False
        self.doc = None
        self.number_field = None
        self.abstract = False
        self.have_validators = False

    def build_attrs_options(self, kwargs):
        if kwargs.get('name') == 'attrs':
            # Include parent attrs in child model definition, pseudo-inheritance
            attrs = next((f['attrs'] for f in (self.parent_model.fields
                                               if self.parent_model else [])
                          if 'attrs' in f),
                         {})
            attrs.update(kwargs['attrs'])
            attrs_lines = []

            diffed_attrs = (
                (name,
                 '\n'.join(makediff_n([d.split('\n')
                                       for d in multidoc.split('\n|')])))
                for name, multidoc in attrs.items()
            )

            def split_prefix(pair):
                name, s = pair
                return [name] + (list(map(str.strip, s.rsplit("::", maxsplit=1))) if "::" in s
                                 else ["", s])

            diffed_attrs_with_prefixes = map(split_prefix, diffed_attrs)

            def prefix_key(triple):
                name, prefix, doc = triple
                return (prefix, name)

            def process_multiline(s, indent=""):
                if '\n' not in s:
                    return s
                return indent_multiline(s, indent=indent + JSON_DOC_INDENT) \
                    .replace('\n', '\n\n').rstrip()

            current_indent = ""

            for prefix, it in groupby(sorted(diffed_attrs_with_prefixes,
                                             key=prefix_key),
                                      key=itemgetter(1)):
                prefix_attrs = list(it)
                if prefix:
                    if current_indent or len(prefix_attrs) > 1:
                        attrs_lines.append("%s%s\n" %
                                           (JSON_GROUP_HEADING,
                                            process_multiline(prefix)))
                        current_indent = JSON_DOC_INDENT
                    else:
                        prefix_attrs = [(name, 0, "::".join((prefix, doc)))
                                        for name, _, doc in prefix_attrs]
                for name, _, doc in prefix_attrs:
                    attrs_lines.append('%s%s``%s`` \u2013 %s\n' %
                                       (current_indent,
                                        "*".ljust(len(JSON_DOC_INDENT)),
                                        name,
                                        process_multiline(doc,
                                                          current_indent)))
            attrs_str = '\n'.join(attrs_lines)
            kwargs['doc'] = [JSON_DOC_HEADING + attrs_str]
            kwargs['options'] = dict(null="True")

    def normalize_field_options(self, kwargs):
        if 'drop' in kwargs:
            return {}
        options = kwargs.get('options', {}).copy()
        doc = kwargs.get('doc', None) or [kwargs['name']]
        if type(doc) is not list:
            kwargs['doc'] = [doc]
        doc = tuple(doc) if type(doc) is list else doc
        if '_' in options:
            if options['_'].startswith('"'):
                options['_'] = stringify(doc, MAX_LINE_LENGTH - 8)
            else:
                options['verbose_name'] = stringify(doc, MAX_LINE_LENGTH - 23)
            return options
        return dict(options, _=stringify(doc, MAX_LINE_LENGTH - 8))

    def build_field_code(self, kwargs, force=False):
        self.build_attrs_options(kwargs)
        skip_code = False
        if force or 'code' not in kwargs:
            tmpl_key = next((k for k in ('drop', 'parent_field',
                                         'one_to_many', 'one_to_one',
                                         'wrap')
                             if k in kwargs),
                            'default')

            final_django_field = kwargs.get('django_field')
            options = self.normalize_field_options(kwargs)
            kwargs['options'] = options.copy()
            kwargs['wrap_options'] = 'null=True' if 'wrap' in kwargs else ''
            if final_django_field == 'models.CharField' and \
                    int(options.get('max_length', 1000)) > 500:
                final_django_field = 'models.TextField'
            if (options.get('null') == "True" and
                ('wrap' in kwargs or
                 final_django_field == 'models.ManyToManyField')):
                del options['null']
            elif final_django_field == 'models.TextField' \
                    and 'max_length' in options:
                del options['max_length']

            if kwargs.get('coalesce'):
                kwargs['code'] = multiline_comment(FIELD_TMPL['_coalesce'].format(**kwargs))
                skip_code = any(('coalesce' in f and
                                 f['coalesce'] == kwargs['coalesce'] and
                                 'code' in f and
                                 ' = ' in f['code'])
                                for f in self.fields)
            else:
                if 'coalesce' in kwargs:
                    del kwargs['coalesce']
                if kwargs.get('dotted_name') and \
                        kwargs.get('name') and \
                        kwargs.get('name') != kwargs['dotted_name'].replace('.', '_'):
                    kwargs['code'] = multiline_comment(FIELD_TMPL['_coalesce']
                                                       .format(coalesce=kwargs.get('name'),
                                                               **kwargs))
                else:
                    kwargs['code'] = ''

            if len(kwargs.get('name', '')) > 63 and \
                    kwargs.get('django_field') not in ('models.ManyToManyField',):
                kwargs['code'] += multiline_comment(
                    "FIXME: %(name)s hits PostgreSQL column name 63 char limit!\n" % kwargs
                )

            if not skip_code:
                def serialized(options):
                    return sorted(v if k == "_" else "{}={}".format(k, v)
                                  for k, v in options.items())

                serialized_options = ', '.join(serialized(options))
                tmpl_ctx = dict(kwargs,
                                options0=options.get("_"),
                                final_django_field=final_django_field,
                                serialized_options=serialized_options)
                tmpl_row = next((r for r in FIELD_TMPL[tmpl_key].split('\n')
                                 if '{serialized_options}' in r), None)
                if tmpl_row:
                    templated_line = tmpl_row.format(**tmpl_ctx)
                    add_indent = '    ' if templated_line.index('(') > MAX_LINE_LENGTH - 1 else ''
                    if len(templated_line) > MAX_LINE_LENGTH:
                        cmt = '# ' if tmpl_row[4] == '#' else ''
                        indent = '    %s    %s' % (cmt, add_indent)
                        newline_indent = "\n" + indent
                        joiner = "," + newline_indent
                        tmpl_ctx['serialized_options'] = \
                            '\n    %s    %s%s\n    %s%s' \
                            % (cmt, add_indent,
                               joiner.join(serialized({k.replace("\n", newline_indent):
                                                       str(v).replace("\n", newline_indent)
                                                       for k, v in options.items()})),
                               cmt, add_indent)
                templated_code = FIELD_TMPL[tmpl_key].format(**tmpl_ctx)
                if tmpl_key == 'default' and templated_code.index('(') > MAX_LINE_LENGTH - 1:
                    cmt = '# ' if templated_code[4] == '#' else ''
                    indent = '    %s    ' % cmt
                    newline_indent = "\n" + indent
                    templated_code = templated_code.replace('= ', '= \\' + newline_indent)
                kwargs['code'] += templated_code
                if 'validators' in options:
                    self.have_validators = True

    def build_code(self):
        model_options = get_opt(self.model_name, self.type_name)
        meta_ctx = {'model_lower': self.model_name.lower()}
        meta = [template % meta_ctx
                for template in chain(model_options.get('meta', []),
                                      GLOBAL_MODEL_OPTIONS.get('meta', []))
                if not (self.abstract and template.startswith('db_table = '))]

        if self.doc and not any(option for option in meta
                                if option.startswith('verbose_name = ')):
            doc = tuple(self.doc) if type(self.doc) is list else self.doc
            doc1 = stringify(doc, MAX_LINE_LENGTH - 23)
            if '\n' in doc1:
                doc1 = stringify(doc, MAX_LINE_LENGTH - 12)
                indent = " " * 4
                doc1 = '({doc}{indent}{indent})'.format(
                    doc=indent_multiline(doc1, indent=indent * 3),
                    indent=indent,
                )
            meta.append('verbose_name = %s' % doc1)

        if self.abstract and not any(option for option in meta
                                     if option.startswith('abstract = ')):
            meta.append('abstract = True')

        indexes = list(chain(
            ['models.Index(fields=["%s", "%s"])' % (f, model_options.get('primary_key', 'id'))
             for f in model_options.get('strict_index_fields', [])],
            ['GinIndex(fields=["%s"])' % f
             for f in model_options.get('gin_index_fields', [])],
            ['models.Index(fields=["%s"])' % f
             for f in list(set(model_options.get('plain_index_fields', [])) -
                           set(model_options.get('unique_fields', [])))
             if f != model_options.get('primary_key')],
        ))
        if indexes:
            meta.append('indexes = [\n            %s\n        ]'
                        % ',\n            '.join(sorted(indexes)))

        if len(meta):
            meta = ('\n\n    class Meta%s:\n%s' %
                    (('(%s.Meta)' % self.parent) if self.parent else '',
                     '\n'.join('        %s' % x for x in sorted(meta))))
        else:
            meta = ''

        methods = '\n\n'.join(model_options.get('methods', ()))
        if methods:
            methods = '\n\n' + methods

        one_to_many_fields = [f for f in self.fields if 'one_to_many' in f]
        one_to_many_descriptions = [
            ' ' * 8 + stringify(name) + ": " +
            stringify(tuple(chain.from_iterable(
                _['doc']
                for _ in one_to_many_fields if _['name'] == name
            )), MAX_LINE_LENGTH - 12) + ",\n"
            for name in sorted(set(f['name'] for f in one_to_many_fields))
        ]
        one_to_many_descriptions = (
            '    AUTO_ONE_TO_MANY_FIELDS = {\n' +
            ''.join(_.replace(": ", ":\n", 1).replace("\n", "\n            ").rstrip() + "\n"
                    if len(_) > MAX_LINE_LENGTH else _
                    for _ in one_to_many_descriptions) +
            '    }\n'
        ) if one_to_many_descriptions else ''
        sorted_fields = self.fields
        if GLOBAL_MODEL_OPTIONS.get('reverse_fields'):
            sorted_fields = sorted(self.fields,
                                   key=lambda f: f.get('dotted_name', f.get('name', ''))[::-1])
        content = ''.join([one_to_many_descriptions,
                           '\n'.join(f['code'] for f in sorted_fields).rstrip(),
                           meta,
                           methods])
        if not content:
            content = '    pass'

        code = '\n\n{cmt}class {name}({parent}):\n{content}\n'.format(
            cmt=multiline_comment('Corresponds to XSD type[s]: ' + self.type_name, indent=0),
            name=self.model_name,
            parent=self.parent or 'models.Model',
            content=content,
        )
        self.code = code

    def add_field(self, **kwargs):
        def fix_related_name(m, django_field, kwargs):
            is_related = partial(RE_RELATED_FIELD.match)
            if is_related(django_field):
                options = kwargs['options']
                name = kwargs['name']

                def model_has_other_related_field(model, name):
                    return any(
                        f for f in m.fields
                        if (is_related(f.get('django_field', '')) and
                            f['options']['_'] == options['_'] and
                            f['name'] != name)
                    )

                if 'related_name' not in options:
                    while m:
                        if model_has_other_related_field(m, name):
                            options['related_name'] = '"%s_as_%s"' % (
                                camelcase_to_underscore(self.model_name),
                                name
                            )
                            return
                        m = m.parent_model

        if not kwargs:
            return

        if kwargs.get('drop_after'):
            return

        if kwargs.get('one_to_one') or kwargs.get('one_to_many'):
            reverse_name = camelcase_to_underscore(self.model_name)
            kwargs = dict(kwargs,
                          reverse_id_name=reverse_name + "_id")

        if 'django_field' in kwargs:
            django_field = kwargs['django_field']

            fix_related_name(self, django_field, kwargs)
            kwargs['django_basefield'] = django_field
            for f in self.builder.fields.values():
                if f['name'] == django_field:
                    kwargs['django_basefield'] = f['parent']
                    break
            else:
                def _set_base(f):
                    kwargs['django_basefield'] = f['parent']

                self.builder.on_field_class(django_field, _set_base)

        self.build_field_code(kwargs)

        self.fields.append(kwargs)

    def make_related_model(self,
                           name=None,
                           one_to_one=False,
                           one_to_many=False,
                           rel=None,
                           **kwargs):
        related_typename, ct_def = rel
        fk = dict(name=camelcase_to_underscore(self.model_name),
                  options=dict(_="'%s'" % self.model_name,
                               on_delete='models.CASCADE',
                               related_name='"%s"' % name,
                               **({'primary_key': 'True'} if one_to_one else {})),
                  doc=self.doc or [],
                  django_field=('models.OneToOneField' if one_to_one
                                else 'models.ForeignKey'))
        self.builder.make_model(related_typename, ct_def, add_fields=[fk])
        return get_model_for_type(related_typename)

    def get(self, dotted_name=None, name=None, **kwargs):
        if dotted_name and name:
            for f in self.fields:
                if f.get('dotted_name') == dotted_name and \
                        f.get('name') == name:
                    return f
        else:
            for f in self.fields:
                if dotted_name and f.get('dotted_name') == dotted_name:
                    return f
                elif name and f.get('name') == name:
                    return f
        return None


class XSDModelBuilder:

    def __init__(self, infile, custom_fields=False):
        self.types = set()
        self.models = {}
        self.fields = {}
        self.have_array = False
        self.have_datetime = False
        self.have_json = False
        self.on_field_class_cb = {}
        self.custom_fields = bool(custom_fields)
        try:
            with open(infile + ".pickle", "rb") as f:
                self.schema = pickle.load(f)
        except Exception:
            pass
        else:
            return

        self.schema = xmlschema.XMLSchema(infile)

        with open(infile + ".pickle", "wb") as f:
            pickle.dump(self.schema, f)

    def get_parent_ns(self, element):
        ptr = element
        while ptr:
            parent = ptr.parent
            if parent is None and (
                ptr.elem.tag.endswith(("}complexType", "}simpleType")) or
                ptr == element
            ):
                name = ptr.elem.get('name')
                if name and ':' in name:
                    ns, _ = name.split(':')
                    return ns + ':'
            ptr = parent
        return ''

    def get_field_choices_from_enumerations(self, enumerations):
        return [(enumeration.get('value'),
                 get_doc(enumeration, None, None) or enumeration.get('value'))
                for enumeration in enumerations]

    def get_field_data_from_simpletype(self, stype):
        if isinstance(stype, xmlschema.validators.XsdUnion):
            logger.warning("xs:simpleType[name=%s]/xs:union is not supported"
                           " yet",
                           stype.prefixed_name)
            return (get_doc(stype, None, None), "TextField", {})

        basetype = self.global_name(stype.base_type)
        try:
            doc, parent, options = (get_doc(stype, None, None),
                                    BASETYPE_FIELD_MAP[basetype],
                                    {})
        except KeyError:
            doc, parent, options = self.get_field_data_from_type(self.simplify_ns(basetype))
        assert type(options) is dict, \
            "options is not a dict while processing type %s" % basetype

        def parsedate(d):
            d = str(d)
            return ('datetime.date(%d, %d, %d)' % (int(d[0:4]), int(d[5:7]),
                                                   int(d[8:10])))

        validators = []
        facets = xmlschema.validators.facets
        for v in stype.validators:
            if isinstance(v, facets.XsdEnumerationFacets):
                choices = self.get_field_choices_from_enumerations(v._elements)
                is_int = parent in ('SmallIntegerField', 'IntegerField', 'BigIntegerField')
                options['choices'] = \
                    '[\n    %s\n]' % ',\n    '.join(
                        '(%s, %s)' %
                        ((c[0] if is_int else ('"%s"' % c[0])),
                         stringify(tuple(c[1]) if type(c[1]) is list
                                   else c[1]))
                        for c in choices
                    )
                if not is_int:
                    options['max_length'] = max(len(c[0]) for c in choices)
            elif isinstance(v, facets.XsdFractionDigitsFacet):
                options['decimal_places'] = v.value
            elif isinstance(v, facets.XsdLengthFacet) and parent != 'IntegerField':
                options['max_length'] = v.value * \
                    GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor', 1)
            elif isinstance(v, facets.XsdMaxExclusiveFacet):
                if parent == 'DateField':
                    self.have_datetime = True
                    arg = parsedate(v.value) + ' - datetime.timedelta(days=1)'
                else:
                    arg = v.value - 1
                validators.append('MaxValueValidator(%s)' % arg)
            elif isinstance(v, facets.XsdMaxInclusiveFacet):
                if parent == 'DateField':
                    self.have_datetime = True
                    arg = parsedate(v.value)
                else:
                    arg = v.value
                validators.append('MaxValueValidator(%s)' % arg)
            elif isinstance(v, facets.XsdMaxLengthFacet):
                options['max_length'] = v.value * \
                    GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor', 1)
            elif isinstance(v, facets.XsdMinExclusiveFacet):
                if parent == 'DateField':
                    self.have_datetime = True
                    arg = parsedate(v.value) + ' + datetime.timedelta(days=1)'
                else:
                    arg = v.value + 1
                validators.append('MinValueValidator(%s)' % arg)
            elif isinstance(v, facets.XsdMinInclusiveFacet):
                if parent == 'DateField':
                    self.have_datetime = True
                    arg = parsedate(v.value)
                else:
                    arg = v.value
                validators.append('MinValueValidator(%s)' % arg)
            elif isinstance(v, facets.XsdMinLengthFacet):
                if v.value == 1:
                    options['blank'] = 'False'
                else:
                    validators.append('MinLengthValidator(%s)' % v.value)
            elif isinstance(v, facets.XsdTotalDigitsFacet):
                if parent == 'DecimalField':
                    options['max_digits'] = v.value
                elif parent == 'IntegerField' and v.value > 9:
                    parent = 'BigIntegerField'
            else:
                raise Exception("Unknown validator facet %s" % v.__class__)

        pattern = '|'.join(stype.patterns.regexps) if stype.patterns else None
        if pattern:
            is_int = parent in ('IntegerField', 'PositiveIntegerField', 'BigIntegerField', 'SmallIntegerField')
            if not is_int and parent not in ('DecimalField', 'FloatField'):
                validators.append('RegexValidator(r"%s")' % pattern)
            if not is_int:
                # Try to infer max_length from regexp
                match = re.match(r'\\d\{(\d+,)?(\d+)\}$', pattern)
                max_length = None
                if match:
                    max_length = match.group(2)
                else:
                    match = re.match(r'(\\d\{\d+\}\|)+\\d\{\d+\}$', pattern)
                    if match:
                        max_length = max(int(match)
                                         for match in re.findall(r'\\d\{(\d+)\}', pattern))
                if max_length:
                    options['max_length'] = int(max_length) * \
                        GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor',
                                                 1)
            if parent == 'DecimalField':
                match = RE_RE_DECIMAL.match(pattern)
                if match:
                    options['decimal_places'] = match.group(6)

        if len(validators):
            options['validators'] = \
                '[%s]' % ', '.join('validators.%s' % x
                                   for x in sorted(validators))
        return doc, parent, options

    def get_field_data_from_type(self, typename):
        if typename in TYPE_OVERRIDES:
            return deepcopy(TYPE_OVERRIDES[typename])
        elif typename in BASETYPE_FIELD_MAP:
            return None, None, None

        try:
            stype = self.get_type(typename)
        except KeyError:
            return None, None, None
        if isinstance(stype, xmlschema.validators.XsdComplexType):
            return None, None, None
        return self.get_field_data_from_simpletype(stype)

    def get_field(self, typename, element=None, el_path=''):
        simplified_typename = self.simplify_ns(typename)
        orig_typename = typename
        if simplified_typename not in self.fields:
            if not typename:
                if isinstance(element.type, xmlschema.validators.XsdComplexType):
                    self.make_model(el_path, element.type)
                    model_name = get_model_for_type(el_path)
                    return orig_typename, {
                        'name': 'models.ForeignKey',
                        'options': dict(_=model_name,
                                        on_delete='models.PROTECT'),
                    }
                elif isinstance(element.type, xmlschema.validators.XsdSimpleType):
                    doc, parent, options = \
                        self.get_field_data_from_simpletype(element.type)
                    try:
                        orig_typename = element.type.primitive_type
                    except AttributeError:  # XsdUnion...
                        orig_typename = 'xs:string'
                    return orig_typename, {
                        'name': 'models.%s' % parent,
                        'options': options,
                    }
                else:
                    raise Exception(
                        "%s nor a simpleType neither a complexType within %s" %
                        (typename, element.name)
                    )

            else:
                typename = (self.global_name(element.type) or
                            self.global_name(element.type.base_type))
                simplified_typename = self.simplify_ns(typename)
                doc, parent, options = self.get_field_data_from_type(simplified_typename)
                if parent is None:
                    if typename in BASETYPE_FIELD_MAP:
                        return orig_typename, {
                            'name': 'models.%s' % BASETYPE_FIELD_MAP[typename]
                        }
                    self.make_model(simplified_typename)
                    return orig_typename, {
                        'name': 'models.ForeignKey',
                        'options': dict(_=get_model_for_type(simplified_typename),
                                        on_delete='models.PROTECT'),
                    }
                if 'choices' in options:
                    validator = next(
                        v for v in self.get_type(typename).validators
                        if isinstance(v, xmlschema.validators.facets.XsdEnumerationFacets)
                    )

                    choices = \
                        self.get_field_choices_from_enumerations(validator._elements)
                else:
                    choices = None
                if parent == 'CharField' and \
                        int(options.get('max_length', 1000)) > 500:
                    # Some data does not fit, even if XSD says it should
                    parent = 'TextField'
                if not self.custom_fields:
                    return orig_typename, dict(name='models.' + parent,
                                               options=options,
                                               doc=doc,
                                               **(dict(choices=choices)
                                                  if choices else {}))
                self.make_field_class(simplified_typename, doc,
                                      parent, options, choices)
        stype = self.get_type(typename)
        orig_typename = ("xs:string" if stype is None
                         else self.global_name(stype.primitive_type))
        return orig_typename, self.fields[simplified_typename]

    def get_type(self, typename):
        t = schema_get_type(self.schema, typename)
        if t is None:
            raise KeyError(typename)
        return t

    def global_name(self, type_):
        return xmlschema.helpers.get_prefixed_qname(type_.name,
                                                    self.schema.namespaces)

    def make_field_class(self, typename, doc, parent, options, choices):
        name = RE_FIELD_CLASS_FILTER.sub('_', typename) + 'Field'
        code = 'class {name}(models.{parent}):\n'.format(name=name,
                                                         parent=parent)

        if doc:
            doc1 = stringify(doc)
            if len(doc1) > MAX_LINE_LENGTH - 20:
                doc1 = stringify(doc, MAX_LINE_LENGTH - 8)
            if '\n' in doc1:
                code += '    description = (%s)\n\n' % doc1
            else:
                code += '    description = %s\n\n' % doc1

        if len(options):
            code += '    def __init__(self, *args, **kwargs):\n' + \
                ''.join('        if "%s" not in kwargs:'
                        ' kwargs["%s"] = %s\n' % (k, k, v)
                        for k, v in sorted(options.items())) + \
                '        super(%s, self).__init__(*args, **kwargs)\n\n' % name
        if not doc and not len(options):
            if parent is None:
                code += '    # SOMETHING STRANGE\n'
            else:
                code += \
                    '    # Simple exact redefinition of %s parent!\n' % parent
            code += '    pass\n'

        code += '\n'
        self.fields[typename] = {
            'code': code,
            'name': name,
            'parent': 'models.%s' % parent,
        }
        if choices:
            self.fields[typename]['choices'] = choices
        for cb in self.on_field_class_cb.get(name, []):
            cb(self.fields[typename])

    def on_field_class(self, name, func):
        self.on_field_class_cb.setdefault(name, []).append(func)

    def simplify_ns(self, typename):
        ns = get_ns(typename)
        ns_map = self.schema.namespaces
        if ns and '' in ns_map and ns_map[ns] == ns_map['']:
            return strip_ns(typename)
        return typename

    def get_element_type(self, element):
        t = element.type
        return (t if t.name and t.name != 'xs:anyType' else
                (t.base_type
                 if (isinstance(t, xmlschema.validators.XsdComplexType) and
                     not t.has_simple_content() and
                     t.is_extension() and
                     #(not (len(t.content) and t.content[-1].model in ('choice', 'sequence'))) and
                     len(t.content) < 2)
                 else None))

    def get_element_type_name(self, element):
        el_type = self.get_element_type(element)
        return self.simplify_ns(self.global_name(el_type)) if el_type else None

    def get_element_complex_type(self, element):
        type_ = self.get_element_type(element)
        if isinstance(type_, xmlschema.validators.XsdComplexType):
            return type_
        if isinstance(element.type, xmlschema.validators.XsdComplexType):
            return element.type
        return None

    def get_own_seq_or_choice(self, ctype):
        return (next(iter(ctype.content[1:]), None)
                if ctype.is_extension() and ctype.has_complex_content()
                else ([] if ctype.is_extension() and ctype.has_simple_content()
                      else ctype.content))

    def write_seq_or_choice(self, seq_or_choice, typename,
                            dotted_prefix='',
                            prefix='',
                            doc_prefix='',
                            attrs=None,
                            null=False):
        if seq_or_choice.model == 'choice':
            fields = self.models[typename].fields
            n_start = len(fields)
            self.make_fields(typename, seq_or_choice,
                             dotted_prefix=dotted_prefix,
                             prefix=prefix,
                             doc_prefix=doc_prefix,
                             attrs=attrs,
                             null=True)
            if len(fields) > n_start:
                fields[n_start]['code'] = ('    # xs:choice start\n' +
                                           fields[n_start]['code'])
                fields[-1]['code'] += '\n    # xs:choice end'
        elif seq_or_choice.model == 'sequence':
            self.make_fields(typename, seq_or_choice,
                             dotted_prefix=dotted_prefix,
                             prefix=prefix,
                             doc_prefix=doc_prefix,
                             attrs=attrs,
                             null=null)
        return ''

    def write_attributes(self, ctype, typename,
                         dotted_prefix='',
                         prefix='',
                         doc_prefix='',
                         attrs=None,
                         null=False):
        if ctype is None:
            return
        this_model = self.models[typename]
        for attribute in ctype.attributes.values():
            attr_name = attribute.name or attribute.ref
            dotted_name = '%s@%s' % (dotted_prefix, attr_name)
            name = prefix + attr_name
            use_required = (attribute.use == "required")
            this_model.add_field(
                **self.make_a_field(typename, name, dotted_name,
                                    attribute=attribute,
                                    dotted_prefix=dotted_prefix,
                                    prefix=prefix,
                                    doc_prefix=doc_prefix,
                                    attrs=attrs,
                                    null=null or not use_required)
            )
            if isinstance(attribute, xmlschema.validators.XsdAnyAttribute):
                attrs[''] = "Any additional attributes"

    def get_n_to_many_relation(self, typename, name, element):
        if element.max_occurs == MAX_OCCURS_UNBOUNDED:
            el2 = element
            el2_name = name
        else:
            ctype = self.get_element_complex_type(element)
            own_seq = self.get_own_seq_or_choice(ctype)
            el2 = own_seq[0] if own_seq else None
            if el2 and el2.max_occurs == MAX_OCCURS_UNBOUNDED:
                el2 = el2.ref or el2
                el2_name = '%s_%s' % (name, el2.local_name)
            else:
                if (
                    el2 is not None and
                    name == el2.local_name + 's' and
                    len(own_seq) + len(ctype.attributes) == 1
                ):
                    el2 = el2.ref or el2
                    el2_name = '%s_%s' % (name, el2.local_name)
                else:
                    el2 = element
                    el2_name = name
                logger.warning("no maxOccurs=unbounded in %s,"
                               " pretending it's unbounded",
                               el2_name)

        ctype2 = self.get_element_complex_type(el2)
        assert ctype2 is not None, \
            "N:many field %s content not a complexType" % name

        rel = self.simplify_ns(self.global_name(ctype2)) or \
            ('%s.%s' % (typename, el2_name))
        return rel, ctype2

    def get_n_to_one_relation(self, typename, name, element):
        ctype2 = self.get_element_complex_type(element)
        assert ctype2 is not None, \
            "N:1 field %s content is not a complexType" % name

        rel = self.simplify_ns(self.global_name(ctype2)) or \
            ('%s.%s' % (typename, name))
        return rel, ctype2

    def nsify(self, typename, context_def):
        return (typename if ':' in typename
                else (self.get_parent_ns(context_def) + typename))

    def flatten_ct(self, ctype, typename, **kwargs):
        if ctype.has_simple_content() and ctype.is_restriction():
            logger.warning("xs:complexType[name=%s]/xs:simpleContent"
                           "/xs:restriction is not yet supported",
                           ctype.prefixed_name)

        if not ctype.has_simple_content() and ctype.is_extension():
            ctype2 = ctype.base_type
            self.flatten_ct(ctype2, typename, **kwargs)

        self.write_attributes(ctype, typename, **kwargs)

        seq_or_choice = self.get_own_seq_or_choice(ctype)
        if seq_or_choice:
            self.write_seq_or_choice(seq_or_choice, typename, **kwargs)
        elif ctype.is_extension():
            logger.warning("xs:complexContent/xs:extension adds nothing to the base type %s",
                           self.global_name(ctype.base_type))
        return (self.global_name(ctype.base_type)
                if ctype.has_simple_content() else None)

    def is_eligible_n2m(self, typename, name, element, n):
        if element is None:
            return False
        if element.max_occurs == MAX_OCCURS_UNBOUNDED:
            return True
        ctype2 = self.get_element_complex_type(element)
        if ctype2 is not None and \
                ctype2.has_complex_content() and \
                len(ctype2.content) == 1 and \
                ctype2.content[0].max_occurs == MAX_OCCURS_UNBOUNDED and \
                not (isinstance(ctype2.content[0], xmlschema.validators.XsdGroup) and
                     ctype2.content[0].model == 'choice'):
            t3_name = self.simplify_ns(self.global_name(ctype2.content[0].type))
            model = get_model_for_type(t3_name or "%s.%s" % (typename, name))
            # If referencing one of our explicit target types, then it's an eligible many-to-many
            # field, otherwise it's an eligible one-to-many field:
            return any(get_model_for_type(t) == model
                       for t in self.target_typenames) != (n == 1)
        return False

    def make_a_field(self, typename, name, dotted_name,
                     element=None,
                     attribute=None,
                     dotted_prefix='',
                     prefix='',
                     doc_prefix='',
                     attrs=None,
                     null=False):
        model_name = get_model_for_type(typename)
        this_model = self.models[typename]
        model = dict({'strategy': GLOBAL_MODEL_OPTIONS.get('strategy', 0)},
                     **get_opt(model_name, typename))
        el_attr = ((attribute.ref or attribute) if element is None
                   else (element.ref or element))
        el_type = self.get_element_type_name(el_attr)
        coalesced_dotted_name = dotted_name

        if match(name, model, 'drop_fields'):
            return dict(dotted_name=dotted_name, drop=True)
        elif model.get('parent_field') == name:
            return dict(dotted_name=dotted_name, parent_field=True)

        def do_coalesce(name, *options):
            nonlocal coalesce_target
            _name = name
            for option in options:
                coalesce_target = \
                    coalesce(_name, model, option) or coalesce_target
                if coalesce_target:
                    _name = coalesce_target
            return (_name,
                    coalesce_target,
                    (coalesce_target if coalesce_target and name == dotted_name
                     else dotted_name))

        drop_after = match(name, model, 'drop_after_processing_fields')
        coalesce_target = None
        if not drop_after:
            name, coalesce_target, coalesced_dotted_name = \
                do_coalesce(name, 'level1_substitutions', 'coalesce_fields')

        assert isinstance(model.get('flatten_fields', ()),
                          (tuple, list, set)), \
            ("flatten_fields should be a tuple/list/set, got %s instead"
             % repr(model['flatten_fields']))
        flatten = match(name, model, 'flatten_fields')
        flatten_name = name

        drop_after = drop_after or \
            match(name, model, 'drop_after_processing_fields')
        if not drop_after:
            name, coalesce_target, coalesced_dotted_name = do_coalesce(name, 'level3_substitutions')

        doc = get_doc(el_attr, name, model_name, doc_prefix=doc_prefix)

        if match(name, model, 'one_to_one_fields'):
            field = dict(dotted_name=dotted_name,
                         one_to_one=True,
                         typename=typename,
                         name=name,
                         drop_after=drop_after,
                         doc=[doc] if doc else [])
            rel = self.get_n_to_one_relation(typename, name, element)
            field['options'] = \
                dict(_=this_model.make_related_model(rel=rel, **field))
            return field

        elif match(dotted_name, model, 'json_fields'):
            if not drop_after:
                attrs[dotted_name] = doc
            return {}

        elif (match(name, model, 'one_to_many_fields') or
              match(name, model, 'one_to_many_field_overrides')) or (
            model.get('strategy', 0) >= 1 and
            not flatten and
            name not in model.get('array_fields', {}) and
            name not in model.get('many_to_many_fields', {}) and
            name not in model.get('many_to_many_field_overrides', {}) and
            self.is_eligible_n2m(typename, name, element, 1)
        ):
            overrides = model.get('one_to_many_field_overrides', {})
            one_to_many = overrides.get(name, True)
            field = dict(dotted_name=dotted_name,
                         one_to_many=one_to_many,
                         typename=typename,
                         name=name,
                         drop_after=drop_after,
                         doc=[doc] if doc else [])
            rel = (
                self.get_n_to_many_relation(typename, name, element)
                if type(one_to_many) is bool
                else (one_to_many, None)
            )
            field['options'] = \
                dict(_=this_model.make_related_model(rel=rel, **field))
            return field

        elif (match(name, model, 'many_to_many_fields') or
              match(name, model, 'many_to_many_field_overrides')) or (
            model.get('strategy', 0) >= 1 and
            not flatten and
            name not in model.get('array_fields', {}) and
            self.is_eligible_n2m(typename, name, element, 2)
        ):
            try:
                rel = model.get('many_to_many_field_overrides', {})[name]
                ctype2 = None
            except KeyError:
                rel, ctype2 = self.get_n_to_many_relation(typename, name,
                                                          element)
            self.make_model(rel, ctype2)
            options = dict(_=get_model_for_type(rel))
            options = override_field_options(name, options, model, 'models.ManyToManyField')
            return dict(dotted_name=dotted_name,
                        name=name,
                        drop_after=drop_after,
                        django_field='models.ManyToManyField',
                        doc=[doc] if doc else [],
                        options=options,
                        coalesce=coalesce_target)

        if element is not None:
            ctype2 = self.get_element_complex_type(element)
            flatten_prefix = \
                flatten_name.startswith(cat(o.get('flatten_prefixes', ())
                                            for o in (GLOBAL_MODEL_OPTIONS,
                                                      model)))

            if (
                not flatten and
                ctype2 is not None and
                model.get('strategy', 0) >= 1 and
                name not in model.get('foreign_key_overrides', {}) and
                name not in model.get('reference_extension_fields', ()) and
                name not in model.get('array_fields', ()) and
                element.max_occurs != MAX_OCCURS_UNBOUNDED
            ):
                ct2_name = self.simplify_ns(self.global_name(ctype2))
                if (ct2_name not in self.target_typenames) and \
                        not get_model_for_type(ct2_name or
                                               '%s.%s' % (typename, name)):
                    flatten = True
            if (ctype2 is not None and flatten_prefix) or flatten:
                doc = get_doc(el_attr, flatten_name, model_name,
                              doc_prefix=doc_prefix) or flatten_name
                o = {
                    'dotted_prefix': '%s.' % dotted_name,
                    'prefix': '%s_' % flatten_name,
                    'doc_prefix': '%s::%s' % (doc, ('\n' if len(doc) > 32 else '')),
                    'attrs': attrs,
                }
                if ctype2 is not None:
                    o['null'] = null or get_null(element)
                    simpletype_base = self.flatten_ct(ctype2, typename, **o)
                    if not simpletype_base:
                        return {}
                    el_type = simpletype_base
                else:
                    logger.warning('complexType not found'
                                   ' while flattening prefix %s',
                                   o['prefix'])

        if not (len(name) <= 63 or drop_after):
            logger.warning("%s hits PostgreSQL column name 63 char limit!" %
                           name)

        basetype = None
        reference_extension = match(name, model, 'reference_extension_fields')
        if reference_extension:
            new_dotted_prefix = '%s.' % dotted_name
            new_prefix = '%s_' % flatten_name
            assert ctype2 is not None, (
                'complexType not found while processing reference extension'
                ' for prefix %s' % new_dotted_prefix
            )
            if ctype2.is_extension():
                basetype = self.global_name(ctype2.base_type)
            else:
                logger.warning("No reference extension while processing prefix"
                               " %s, falling back to normal processing",
                               new_dotted_prefix)
                reference_extension = False

        if match(name, model, 'array_fields'):
            if ctype2 is not None:
                final_el_attr = next(chain(ctype2.attributes.values(),
                                           ctype2.content))
                ctype3 = self.get_element_complex_type(final_el_attr)
                if ctype3 and len(ctype3.content) == 1:
                    final_el_attr = ctype3.content[0]
                final_type = self.get_element_type_name(final_el_attr)
            else:
                assert element.max_occurs == MAX_OCCURS_UNBOUNDED, (
                    '%s has no maxOccurs=unbounded or complexType, required '
                    'for array_fields'
                    % dotted_name
                )
                final_el_attr = el_attr
                final_type = basetype or el_type
            doc = get_doc(final_el_attr, name, model_name,
                          doc_prefix=doc + '::')
        else:
            final_el_attr = el_attr
            final_type = basetype or el_type

        try:
            rel = model.get('foreign_key_overrides', {})[name]
        except KeyError:
            final_type, field = self.get_field(final_type,
                                               final_el_attr,
                                               '%s.%s' % (typename, name))
        else:
            if rel != '%s.%s' % (typename, name):
                try:
                    fk_ctype = self.get_type(rel)
                except KeyError:
                    fk_ctype = self.get_n_to_one_relation(typename, name,
                                                          element)[1]
            else:
                rel, fk_ctype = self.get_n_to_one_relation(typename, name,
                                                           element)
            self.make_model(rel, fk_ctype)
            field = {
                'name': 'models.ForeignKey',
                'options': dict(_=get_model_for_type(rel),
                                on_delete='models.PROTECT'),
            }

        choices = field.get('choices', [])
        if any(c[0] not in (doc or '') for c in choices):
            doc = get_doc(el_attr, name, model_name,
                          doc_prefix=doc_prefix, choices=choices)

        over_class = override_field_class(model_name, typename, name)
        if over_class:
            field = {'name': over_class,
                     'options': field.get('options', {})}

        options = field.get('options', {})

        new_null = null or match(name, model, 'null_fields')
        if new_null:
            if name == model.get('primary_key', None):
                logger.warning("WARNING: %s.%s is a primary key but has"
                               " null=True. Skipping null=True",
                               model_name, name)
            else:
                options['null'] = 'True'
        else:
            default = (final_el_attr.default or
                       final_el_attr.fixed)
            if default:
                try:
                    default = parse_default(final_type, default)
                except Exception as e:
                    raise ValueError("%s while parsing default for %s.%s" %
                                     (type(e), model_name, name)) from e
                options['default'] = repr(default)

        if match(name, model, 'array_fields'):
            field = dict(field, wrap='ArrayField')
            self.have_array = True

        if element is not None:
            max_occurs = element.max_occurs
            assert \
                (max_occurs == 1) or (field.get('wrap') == "ArrayField"), (
                    "caught maxOccurs=%s in %s.%s (@type=%s). Consider adding"
                    " it to many_to_many_fields, one_to_many_fields,"
                    " array_fields, or json_fields" %
                    ('unbounded' if max_occurs == MAX_OCCURS_UNBOUNDED else max_occurs,
                     typename, name, el_type)
                )

        if name == model.get('primary_key', None):
            options['primary_key'] = 'True'
            this_model.number_field = name
        elif match(name, model, 'unique_fields'):
            options['unique'] = 'True'
        if match(name, model, 'index_fields'):
            options['db_index'] = 'True'
        elif (match(name, model, 'gin_index_fields') or
              match(name, model, 'plain_index_fields') or
              match(name, model, 'strict_index_fields')):
            options['db_index'] = 'INDEX_IN_META'
        options = override_field_options(name, options, model, field['name'])

        if reference_extension:
            self.write_seq_or_choice(self.get_own_seq_or_choice(ctype2), typename,
                                     dotted_prefix=new_dotted_prefix,
                                     prefix=new_prefix,
                                     doc_prefix=doc_prefix,
                                     attrs=attrs,
                                     null=null)

        return dict({'wrap': field['wrap']} if field.get('wrap', 0) else {},
                    dotted_name=dotted_name,
                    name=name,
                    doc=[doc] if doc else [],
                    django_field=field['name'],
                    options=options,
                    drop_after=drop_after,
                    coalesce=coalesce_target)

    def make_fields(self, typename, seq_def,
                    dotted_prefix='',
                    prefix='',
                    doc_prefix='',
                    attrs=None,
                    null=False):
        this_model = self.models[typename]
        null = (null or get_null(seq_def))

        for el in seq_def:

            if isinstance(el, xmlschema.validators.XsdAnyElement):
                attrs[''] = "Any additional elements"
                continue

            if not isinstance(el, xmlschema.validators.XsdElement):
                self.write_seq_or_choice(el, typename,
                                         dotted_prefix=dotted_prefix,
                                         prefix=prefix,
                                         doc_prefix=doc_prefix,
                                         attrs=attrs,
                                         null=null)
                continue

            el_name = el.local_name or el.ref
            dotted_name = dotted_prefix + el_name
            name = prefix + el_name

            this_model.add_field(
                **self.make_a_field(typename, name, dotted_name,
                                    element=el,
                                    dotted_prefix=dotted_prefix,
                                    prefix=prefix,
                                    doc_prefix=doc_prefix,
                                    attrs=attrs,
                                    null=null or get_null(el))
            )

    def get_parent_type_name_from_ct(self, ctype):
        seq_or_choice = self.get_own_seq_or_choice(ctype)
        if not seq_or_choice and not ctype.is_extension() and \
                not ctype.attributes:
            logger.warning("no sequence/choice, no attributes, and"
                           " no complexContent in %s complexType",
                           ctype.prefixed_name)
        elif not seq_or_choice and ctype.is_extension():
            n_attributes = len(ctype.attributes)
            complexity = ("complex" if ctype.has_complex_content() else "simple")
            ext_def = xfind(ctype.elem, "xs:%sContent/xs:extension" % complexity)[0]
            assert len(ext_def) == n_attributes, (
                "no sequence or choice and no attributes in"
                " extension in complexContent in %s complexType"
                " but %d other children exist"
                % (ctype.prefixed_name, len(ext_def) - n_attributes)
            )
            if not n_attributes:
                logger.warning("no additions in extension in"
                               " complexContent in %s complexType",
                               ctype.prefixed_name)

        parent = None
        if ctype.is_extension():
            parent = self.simplify_ns(self.global_name(ctype.base_type))
            assert parent, (
                "no base attribute in extension in %s complexType"
                % ctype.prefixed_name
            )

        return parent

    def make_model(self, typename, ctype=None, add_fields=None):
        global depth
        depth += 1

        model_name = get_model_for_type(typename)
        if not model_name:
            logger.warning('Automatic model name: %s. Consider adding it to'
                           ' TYPE_MODEL_MAP\n',
                           typename)
            TYPE_MODEL_MAP[typename.replace('.', r'\.')] = typename
            model_name = get_model_for_type(typename)

        if typename in self.types:
            depth -= 1
            return

        self.types.add(typename)

        model = get_opt(model_name, typename)

        info('Making model for type %s\n' % typename)

        if typename not in self.models:
            this_model = Model(self, model_name, typename)
            self.models[typename] = this_model
        else:
            assert get_merge_for_type(typename), (
                "Not merging type %s, model %s already exists and no merge (+)"
                " prefix specified" % (typename, model_name)
            )

        parent_type = None
        deps = []
        attrs = {}

        if not model.get('custom', False):
            if ctype is None:
                try:
                    ctype = self.get_type(typename)
                except KeyError:
                    raise Exception("%s not found in schema" % typename)

            this_model.abstract = (model.get('abstract', False) or
                                   ctype.abstract)

            if ctype.mixed:
                logger.warning(
                    'xs:complexType[name="%s"] mixed=true is not supported'
                    ' yet',
                    typename
                )
            if ctype.has_simple_content():
                logger.warning(
                    'xs:complexType[name="%s"]/xs:simpleContent is only'
                    ' supported within flatten_fields',
                    typename
                )
            if ctype.has_restriction():
                logger.warning(
                    'xs:complexType[name="%s"]/xs:complexContent'
                    '/xs:restriction is not supported yet',
                    typename
                )

            doc = get_doc(ctype, None, None)
            if not doc:
                if ctype.parent and isinstance(ctype.parent, xmlschema.validators.XsdElement):
                    doc = get_doc(ctype.parent, None, None)
            this_model.doc = [doc] if doc else None

            parent_type = self.get_parent_type_name_from_ct(ctype)
            if not parent_type:
                parent_field = model.get('parent_field')
                if parent_field:
                    try:
                        parent_type = next(self.global_name(el.type)
                                           for el in ctype.content
                                           if el.local_name == parent_field)
                    except StopIteration:
                        raise Exception(
                            'parent_field is set for %s but not found'
                            % typename
                        )

            self.write_attributes(ctype, typename, attrs=attrs)

        if 'parent_type' in model:
            parent_type = model['parent_type']

        if model.get('include_parent_fields') and not parent_type:
            logger.warning(
                "include_parent_fields, but parent not found in %s", typename
            )
        if parent_type and parent_type in BASETYPE_FIELD_MAP:
            # Probably simpleContent.
            # Add same-named field, with all substitutions.
            coalesced_name = ctype.parent.local_name
            for option in ('level1_substitutions', 'coalesce_fields',
                           'level3_substitutions'):
                coalesced_name = \
                    coalesce(coalesced_name, model, option) or coalesced_name
            this_model.add_field(django_field='models.%s' % BASETYPE_FIELD_MAP[parent_type],
                                 name=coalesced_name,
                                 dotted_name=ctype.parent.local_name,
                                 doc=doc,
                                 options=[])
        elif parent_type:
            if model.get('include_parent_fields'):
                parent = self.get_type(parent_type)
                self.write_seq_or_choice(parent.content, typename,
                                         attrs=attrs)
            else:
                self.make_model(parent_type)
                if not this_model.parent_model:
                    this_model.parent_model = self.models[parent_type]
                parent_model_name = get_model_for_type(parent_type)
                deps.append(parent_model_name)
                if not this_model.parent:
                    this_model.parent = parent_model_name

        if not model.get('custom', False):
            seq_or_choice = self.get_own_seq_or_choice(ctype)
            if seq_or_choice:
                self.write_seq_or_choice(seq_or_choice, typename, attrs=attrs)

        for f in chain(model.get('add_fields', []),
                       add_fields or []):
            related_typename = f.get('one_to_many') or f.get('one_to_one')
            f['options'] = parse_user_options(f.get('options', []))
            if related_typename:
                assert type(related_typename) is not bool, (
                    "one_to_many or one_to_one within add_fields should be a"
                    " typename not bool"
                )
                f['options'] = dict(
                    _=this_model.make_related_model(
                        rel=(related_typename, None),
                        **f),
                )
            elif f.get('django_field') in ('models.ForeignKey',
                                           'models.ManyToManyField'):
                dep_name = get_a_type_for_model(f['options']['_'], self.schema)
                if dep_name:
                    self.make_model(dep_name)
            this_model.add_field(**f)

        for attr_name, attr_doc in \
                model.get('add_json_attrs', {}).items():
            attrs[attr_name] = attr_doc

        if len(attrs):
            this_model.add_field(name='attrs',
                                 django_field='JSONField',
                                 attrs=attrs)
            self.have_json = True

        for f in this_model.fields:
            if f.get('django_field') in ('models.ForeignKey',
                                         'models.OneToOneField',
                                         'models.ManyToManyField'):
                if not f['options']['_'].startswith("'"):
                    deps.append(f['options']['_'])
        this_model.deps = list(set(deps + (this_model.deps or [])))

        if not this_model.number_field:
            try:
                this_model.number_field = model['number_field']
            except KeyError:
                if this_model.parent_model:
                    this_model.number_field = \
                        this_model.parent_model.number_field

        this_model.build_code()

        if 'match_fields' in model:
            this_model.match_fields = model['match_fields']

        info('Done making model %s (%s)\n' % (model_name, typename))
        depth -= 1

    def make_models(self, typenames):
        self.target_typenames = typenames
        for typename in typenames:
            if typename.startswith('/'):
                self.make_model('typename1', self.schema.elements[typename[1:]].type)
            else:
                self.make_model(typename)

    def merge_models(self):
        def are_coalesced(field1, field2):
            return any('coalesce' in f1 and
                       f2.get('coalesce', f2.get('name')) == f1['coalesce']
                       for f1, f2 in [(field1, field2), (field2, field1)])

        def squeeze_docs(docs_seq):
            merged = sorted(set(docs_seq))
            prev_doc = None
            processed = []
            for doc in merged:
                if prev_doc:
                    if doc.startswith(prev_doc):
                        del processed[-1]
                processed.append(doc)
                prev_doc = doc
            return processed

        def merge_attrs(m1, f1, m2, f2):
            attrs1 = f1['attrs']
            attrs2 = f2['attrs']
            attrs = {}
            for key in set(chain(attrs1.keys(), attrs2.keys())):
                if key in attrs1 and key in attrs2:
                    attrs[key] = '\n|'.join(squeeze_docs(cat(
                        a[key].split('\n|')
                        for a in (attrs1, attrs2)
                    )))
                else:
                    attrs[key] = attrs1.get(key, attrs2.get(key))
            f1['attrs'] = attrs
            m1.build_field_code(f1, force=True)
            f2['attrs'] = attrs
            m2.build_field_code(f2, force=True)

        def merge_field_docs(model1, field1, model2, field2):
            if 'doc' not in field1 and 'doc' not in field2:
                return
            merged = squeeze_docs(field1.get('doc', []) +
                                  field2.get('doc', []))
            if field1.get('doc', []) != merged:
                field1['doc'] = merged
                model1.build_field_code(field1, force=True)
            if field2.get('doc', []) != merged:
                field2['doc'] = merged
                if model2:
                    model2.build_field_code(field2, force=True)

        def merge_field(name, dotted_name, containing_models, models):
            omnipresent = (len(containing_models) == len(models))

            containing_opts = [m.get(dotted_name=dotted_name,
                                     name=name).get('options', {})
                               for m in containing_models]
            if not omnipresent or any(o.get('null') == 'True'
                                      for o in containing_opts):
                if any(o.get('primary_key') == 'True'
                       for o in containing_opts):
                    logger.warning("Warning: %s is a primary key but wants"
                                   " null=True in %s",
                                   (name, dotted_name), merged_typename)
                else:
                    for m in containing_models:
                        f = m.get(dotted_name=dotted_name, name=name)
                        if 'options' not in f:
                            f['options'] = {}
                        if f['options'].get('null') != 'True':
                            f['options']['null'] = 'True'
                            m.build_field_code(f, force=True)

            first_model_field = None
            for m in containing_models:
                f = m.get(dotted_name=dotted_name, name=name)
                if not first_model_field:
                    first_model_field = f
                    first_model = m
                else:
                    if 'name' in f and f['name'] == 'attrs':
                        merge_attrs(first_model, first_model_field, m, f)
                    else:
                        unify_special_cases(f, first_model_field)
                    merge_field_docs(first_model, first_model_field, m, f)
                    code1, code2 = (normalize_code(f['code']),
                                    normalize_code(first_model_field['code']))
                    if not code1 or not code2:
                        # Looks like one of them is fully coalesced, can concatenate code
                        if first_model_field['code'] in f['code']:
                            first_model_field['code'] = f['code']
                        elif f['code'] in first_model_field['code']:
                            pass
                        else:
                            first_model_field['code'] = first_model_field['code'] + f['code']
                    elif code1 != code2:
                        force_list = get_opt(m.model_name, m.type_name) \
                            .get('ignore_merge_mismatch_fields', ())
                        if f.get('dotted_name') not in force_list:
                            first_model_field['code'] = (
                                '    # FIXME: cannot merge fields:\n'
                                '    # first field in type %s:\n'
                                '%s\n'
                                '    # second field in type %s:\n'
                                '%s\n'
                                '    # EOFIXME\n'
                            ) % (containing_models[0].type_name,
                                 first_model_field['code'],
                                 m.type_name,
                                 f['code'])

            f = first_model_field

            if not omnipresent and not f.get('drop', False):
                if len(containing_models) > len(models) / 2:
                    lacking_models = set(models) - set(containing_models)
                    f['code'] = multiline_comment(
                        "NULL in %s" % ', '.join(sorted(m.type_name for m in lacking_models))
                    ) + f['code']
                else:
                    f['code'] = multiline_comment(
                        "Only in %s" % ', '.join(sorted(m.type_name for m in containing_models))
                    ) + f['code']
            return f

        def merge_model_docs(models):
            docs = sorted(set(cat(m.doc for m in models if m.doc)))
            if len(docs) == 0:
                return None
            return docs

        def merge_model_parents(models, merged_models):
            def fix_related_name(m, f):
                old_relname_prefix = '"%s_as_' \
                    % camelcase_to_underscore(m.model_name)
                options = f.get('options', {})
                option = options.get('related_name', '')
                if option.startswith(old_relname_prefix):
                    options['related_name'] = '"%s_as_%s' \
                        % (camelcase_to_underscore(parents[1]),
                           option[len(old_relname_prefix):])
                    m.build_field_code(f, force=True)

            def check_fields(parent_model, parent_name, m, f, f1):
                parent_opts = get_opt(parent_model.model_name,
                                      parent_model.type_name)
                assert (
                    normalize_code(f1['code']) == normalize_code(f['code']) or
                    (f1.get('dotted_name') in
                     parent_opts.get('ignore_merge_mismatch_fields', ()))
                ), (
                    'different field code while merging:\n%s: %s;\n%s: %s'
                    % (parent_name, f1['code'], m.model_name, f['code'])
                )

            parents = sorted(set((m.parent or '') for m in models))
            if parents[0] == '' and len(parents) == 2:
                parent_model = merged_models[parents[1]]
                for m in models:
                    if m.parent is None:
                        inherited_fields = []
                        for i, f in enumerate(m.fields):
                            f1 = parent_model.get(**f)
                            if f1:
                                if f1.get('name') == 'attrs':
                                    merge_attrs(parent_model, f1, m, f)
                                fix_related_name(m, f)
                                check_fields(parent_model, parents[1],
                                             m, f, f1)
                                inherited_fields.insert(0, i)
                        for i in inherited_fields:
                            del m.fields[i]
                del parents[0]
            return parents

        @memoize
        def normalize_code(s):
            s = s.replace('..', '.')
            s = re.sub(r'(\n?    # xs:choice (start|end)\n?'
                       r'|\n?    # (NULL|Only) in [^\n]+\n'
                       r'|\n?    # [^\n]+ => [^\n]+\n'
                       r'|\n?    # The original [^\n]+\n'
                       r'|\n?    #  [^\n]+\n'
                       r'|,\s+(#\s+)?related_name="[^"]+"'
                       r'|,\s+[a-z_]+=None\b)',
                       '', s)
            return s

        def unify_special_cases(field1, field2):
            for f1, f2 in ((field1, field2), (field2, field1)):
                fk_and_one_to_one = (
                    f1.get('django_field') == 'models.OneToOneField' and
                    f2.get('django_field') == 'models.ForeignKey'
                )

                single_and_array = (
                    f2.get('django_field') == 'ArrayField' and
                    f1.get('django_field') == f2.get('options', {}).get('_')
                )
                if single_and_array:
                    f1['django_field'] = f2['django_field']
                    f1['options']['_'] = f2['options']['_']

                drop_and_add = (f1.get('drop') and not f2.get('drop'))
                if drop_and_add:
                    f2['code'] = \
                        '    # The original {dotted_name} is dropped and' \
                        ' replaced by an added one\n{code}'.format(**f2)

                if any((fk_and_one_to_one, single_and_array, drop_and_add)):
                    if not single_and_array:
                        f1.clear()
                        f1.update(f2)
                    return

        merged_models = dict()
        merged = dict()
        for model in self.models.values():
            merged.setdefault(model.model_name, []).append(model)
        merged1 = dict()
        merged2 = dict()
        for model_name in merged.keys():
            models = merged[model_name]
            if any(m.parent for m in models):
                merged2[model_name] = models
            else:
                merged1[model_name] = models

        for model_name, models in chain(merged1.items(),
                                        merged2.items()):
            if len(models) == 1:
                merged_model = models[0]
            else:
                merged_typename = '; '.join(sorted(m.type_name
                                                   for m in models))
                merged_model = Model(self, model_name, merged_typename)

                merged_model.match_fields = models[0].match_fields
                merged_model.number_field = models[0].number_field

                if all(m.abstract for m in models):
                    merged_model.abstract = True
                else:
                    assert not any(m.abstract for m in models), \
                        "only some of merged types are abstract: %s" % merged_typename


                parents = merge_model_parents(models, merged_models)
                assert len(parents) <= 1, \
                    "different parents %s for types %s" % (parents,
                                                           merged_typename)

                if parents:
                    merged_model.parent = parents[0]

                merged_model.deps = sorted(set(cat(m.deps for m in models
                                                   if m.deps)))

                field_ids = sorted(set((f.get('coalesce', f.get('name')),
                                        ('coalesce' in f),
                                        f.get('dotted_name'))
                                       for f in cat(m.fields for m in models)),
                                   key=lambda _: (_[0] or '', _[1], _[2] or ''))
                field_ids = [(f[0], f[2], [m for m in models
                                           if m.get(dotted_name=f[2],
                                                    name=f[0])])
                             for f in field_ids]

                prev = None
                for name, dotted_name, containing_models in field_ids:

                    f = merge_field(name, dotted_name, containing_models,
                                    models)

                    if prev and are_coalesced(prev, f) \
                            and prev.get('has_code'):
                        # The field coalesces with the previous one, so
                        # keep only comments and docs
                        comment_lines = (line for line in f['code'].split('\n')
                                         if line.startswith('    #'))
                        f['code'] = '\n'.join(comment_lines)
                        merge_field_docs(merged_model, prev, None, f)
                        f['has_code'] = True
                    else:
                        f['code'] = '\n'.join(line
                                              for line in f['code'].split('\n')
                                              if line.strip())
                        f['has_code'] = any(line
                                            for line in f['code'].split('\n')
                                            if not line.startswith('    #'))
                        prev = f
                    merged_model.fields.append(f)

                merged_model.doc = merge_model_docs(models)

            merged_model.build_code()
            merged_models[merged_model.model_name] = merged_model
        self.models = merged_models

    def write_model(self, model, outfile):
        if model.written:
            return
        for dep in sorted(model.deps):
            if dep != model.model_name and not get_opt(dep).get('skip_code'):
                self.write_model(self.models[dep], outfile)
        outfile.write(model.code)
        model.written = True

    def write(self, models_file, fields_file, map_file):
        if fields_file:
            fields_file.write(HEADER)
            fields_file.write('import datetime\n')
            fields_file.write('from django.core import validators\n')
            fields_file.write('from django.db import models\n\n\n')
            for key in sorted(self.fields):
                field = self.fields[key]
                if 'code' in field:
                    fields_file.write(field['code'])

        models_file.write(HEADER)
        if self.have_datetime:
            models_file.write('import datetime\n')
        if any(_.have_validators for _ in self.models.values()):
            models_file.write('from django.core import validators\n')
        models_file.write('from django.db import models\n')
        if self.have_array:
            models_file.write('from django.contrib.postgres.fields import'
                              ' ArrayField\n')
        if self.have_json:
            models_file.write(
                'try:\n'
                '    JSONField = models.JSONField\n'
                'except AttributeError:\n'
                '    from django.contrib.postgres.fields import JSONField\n'
            )
        if any('gin_index_fields' in o for o in MODEL_OPTIONS.values()):
            models_file.write('from django.contrib.postgres.indexes import'
                              ' GinIndex\n')

        models_file.write('\n')
        if fields_file:
            fields = sorted(
                set(f['name'] for f in self.fields.values() if 'code' in f)
                .intersection(f.get('django_field')
                              for f in chain.from_iterable(m.fields
                                                           for n, m in self.models.items()
                                                           if not get_opt(n).get('skip_code')))
            )
            if len(fields):
                models_file.write(
                    'from .fields import \\\n        %s\n'
                    % ', \\\n        '.join(fields)
                )
        models_file.write(IMPORTS + '\n\n\n')
        if any(('gin_index_fields' in o or
                'plain_index_fields' in o or
                'strict_index_fields' in o)
               for o in MODEL_OPTIONS.values()):
            models_file.write('INDEX_IN_META = False  # A handy marker\n')
        for model_name in sorted(self.models.keys()):
            if not get_opt(model_name).get('skip_code'):
                self.write_model(self.models[model_name], models_file)

        mapping = {}
        for m in self.models.values():
            model_mapping = {}
            for key in ('model_name',
                        'fields',
                        'parent',
                        'match_fields',
                        'number_field'):
                value = getattr(m, key)
                if not (value is None or (key == 'parent' and not value)):
                    model_mapping[key] = value
            mapping[m.model_name] = model_mapping
        json.dump(mapping, map_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    try:
        args = docopt(__doc__)

        builder = XSDModelBuilder(args['<xsd_filename>'], args['-f'])
        builder.make_models([(a.decode('UTF-8') if hasattr(a, 'decode') else a)
                             for a in args['<xsd_type>']])
        builder.merge_models()
        builder.write(codecs.open(args['-m'], "w", 'utf-8'),
                      (codecs.open(args['-f'], "w", 'utf-8')
                       if args['-f'] else None),
                      codecs.open(args['-j'], "w", 'utf-8'))
    except Exception as e:
        logger.error('EXCEPTION: %s', str(e))
        type, value, tb = sys.exc_info()
        import traceback
        import pdb
        traceback.print_exc()
        pdb.post_mortem(tb)
        sys.exit(1)
