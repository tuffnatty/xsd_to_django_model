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
    -f <fields_filename>   Output fields filename [default: fields.py].
    -j <mapping_filename>  Output JSON mapping filename [default: mapping.json].
    <xsd_filename>         Input XSD schema filename.
    <xsd_type>             XSD type (or an XPath query for XSD type) for which
                           a Django model should be generated.

If you have xsd_to_django_model_settings.py in your PYTHONPATH or in the current
directory, it will be imported.
"""


import codecs
from copy import deepcopy
import datetime
import decimal
from itertools import chain
import json
import logging
import os.path
import re
import sys

from docopt import docopt
from lxml import etree

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
    from xsd_to_django_model_settings import IMPORTS
except ImportError:
    IMPORTS = ''

BASETYPE_FIELD_MAP = {
    'xs:base64Binary': 'BinaryField',
    'xs:boolean': 'BooleanField',
    'xs:byte': 'SmallIntegerField',
    'xs:date': 'DateField',
    'xs:dateTime': 'DateTimeField',
    'xs:decimal': 'DecimalField',
    'xs:double': 'FloatField',
    'xs:gYearMonth': 'DateField',  # Really YYYY-MM
    'xs:int': 'IntegerField',
    'xs:integer': 'IntegerField',
    'xs:long': 'BigIntegerField',
    'xs:nonNegativeInteger': 'PositiveIntegerField',
    'xs:positiveInteger': 'PositiveIntegerField',
    'xs:short': 'SmallIntegerField',
    'xs:string': 'CharField',
    'xs:token': 'CharField',
}
NS = {'xs': "http://www.w3.org/2001/XMLSchema"}

FIELD_TMPL = {
    '_coalesce':
        '    # %(dotted_name)s field coalesces to %(coalesce)s\n',
    'drop':
        '    # Dropping %(dotted_name)s field',
    'parent_field':
        '    # %(dotted_name)s field translates to this model\'s parent',
    'one_to_many':
        '    # %(name)s is declared as a reverse relation from %(options0)s\n'
        '    # %(name)s = OneToManyField(%(serialized_options)s)',
    'one_to_one':
        '    # %(name)s is declared as a reverse relation from %(options0)s\n'
        '    # %(name)s = OneToOneField(%(serialized_options)s)',
    'wrap':
        '    %(name)s = %(wrap)s(%(final_django_field)s(%(serialized_options)s)'
        ', %(wrap_options)s)',
    'default':
        '    %(name)s = %(final_django_field)s(%(serialized_options)s)',
}

HEADER = ('# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT\n'
          '# -*- coding: utf-8 -*-\n\n'
          'from __future__ import unicode_literals\n\n')

RE_SPACES = re.compile(r'  +')
RE_KWARG = re.compile(r'^[a-zi0-9_]+=')
RE_CAMELCASE_TO_UNDERSCORE_1 = re.compile(r'(.)([A-Z][a-z]+)')
RE_CAMELCASE_TO_UNDERSCORE_2 = re.compile(r'([a-z0-9])([A-Z])')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


depth = -1


def cat(seq):
    return tuple(chain.from_iterable(seq))


def info(s):
    sys.stderr.write('%s%s' % (' ' * depth, s))


def xpath(root, path, **kwargs):
    return root.xpath(path, namespaces=NS, **kwargs)


def get_model_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.iteritems():
        if re.match(expr + '$', name):
            return re.sub(expr + '$', sub, name).replace('+', '')
    return None


def get_a_type_for_model(name):
    plus_name = '+%s' % name
    for expr, sub in TYPE_MODEL_MAP.iteritems():
        if '(' not in expr and '\\' not in expr and sub in (name, plus_name):
            return expr
    return None


def get_merge_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.iteritems():
        if re.match(expr + '$', name):
            return sub.startswith('+')
    return False


def get_opt(model_name, typename=None):
    opt = MODEL_OPTIONS.get(model_name, {})
    if not typename:
        return opt
    for opt2 in (o for pattern, o in opt.get('if_type', {}).iteritems()
                 if re.match(pattern + '$', typename)):
        opt = deepcopy(opt)
        for k, v in opt2.iteritems():
            try:
                v1 = opt[k]
            except KeyError:
                opt[k] = v
            else:
                if type(v1) == dict and type(v) == dict:
                    opt[k] = dict(v1, **v)
                elif isinstance(v1, basestring) and isinstance(v, basestring):
                    opt[k] = v
                else:
                    opt[k] = list(set(chain(v1, v)))
    return opt


def get_doc(el_def, name, model_name, doc_prefix=None):
    name = name or el_def.get('name')
    if model_name:
        try:
            return get_opt(model_name)['field_docs'][name]
        except KeyError:
            pass
    doc = chain(xpath(el_def, "xs:annotation/xs:documentation"),
                xpath(el_def, "xs:complexType/xs:annotation/xs:documentation"))
    doc = (d.text for d in doc if d.text)
    try:
        doc = RE_SPACES.sub(' ', next(doc).strip()).rstrip('.') \
            .replace(' )', ')').replace('\n\n', '\n')
    except StopIteration:
        doc = None
    if doc_prefix is not None:
        return doc_prefix + (doc or name)
    return doc


def stringify(s):
    if type(s) is list:
        s = '|'.join(el.strip() for el in s)
    return '"%s"' % RE_SPACES.sub(' ', s.strip()) \
        .replace('\\', '\\\\') \
        .replace('"', '\\"') \
        .replace('\n\n', '\n') \
        .replace('\n', '\\n"\n"')


def get_null(el_def):
    return el_def.get("minOccurs", None) == "0"


def get_ns(typename):
    if typename and ':' in typename:
        return typename.split(':')[0]
    return ''


def strip_ns(typename):
    if typename and ':' in typename and not typename.startswith("xs:"):
        _, typename = typename.split(':')
    return typename


def camelcase_to_underscore(name):
    s1 = RE_CAMELCASE_TO_UNDERSCORE_1.sub(r'\1_\2', name)
    return RE_CAMELCASE_TO_UNDERSCORE_2.sub(r'\1_\2', s1).lower()


def coalesce(name, model):
    fulldict = dict(GLOBAL_MODEL_OPTIONS.get('coalesce_fields', {}),
                    **model.get('coalesce_fields', {}))
    for expr, sub in fulldict.iteritems():
        match = re.match(expr + '$', name)
        if match:
            return re.sub(expr, sub, name)
    return None


def match(name, model, kind):
    for expr in chain(model.get(kind, ()),
                      GLOBAL_MODEL_OPTIONS.get(kind, ())):
        if re.match(expr + '$', name):
            return True
    return False


def override_field_options(field_name, options, model_options):
    add_field_options = dict(GLOBAL_MODEL_OPTIONS.get('field_options', {}),
                             **model_options.get('field_options', {}))
    if field_name in add_field_options:
        for option in add_field_options[field_name]:
            option_key, _ = option.split('=', 1)
            for n, old_option in enumerate(options):
                if old_option.split('=', 1)[0] == option_key:
                    del options[n]
                    break
        options += add_field_options[field_name]


def override_field_class(model_name, typename, name):
    return get_opt(model_name, typename) \
        .get('override_field_class', {}) \
        .get(name)


def parse_default(basetype, default):
    if basetype == "xs:boolean":
        assert default in ("true", "false"), (
            "cannot parse boolean %s.%s default value: %s"
            % (model_name, name, default)
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
        return long(default)
    if basetype == "xs:string":
        return default
    if basetype == "xs:token":
        return ''.join(default.split())
    if basetype in ("xs:byte", "xs:int", "xs:integer",
                    "xs:nonNegativeInteger", "xs:positiveInteger", "xs:short"):
        return int(default)
    assert False, "parsing default value '%s' for %s type not implemented" \
        % (default, basetype)


def resolve_ref(tree, attr_def, attr_or_el):
    if attr_def is None:
        return None
    ref = attr_def.get('ref')
    if ref:
        return xpath(tree, "//%s[@name=$n]" % attr_or_el, n=ref)[0]
    return attr_def


def resolve_attr_ref(tree, attr_def):
    return resolve_ref(tree, attr_def, "xs:attribute")


def resolve_el_ref(tree, el_def):
    return resolve_ref(tree, el_def, "xs:element")


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

    def build_attrs_options(self, kwargs):
        if kwargs.get('name') == 'attrs':
            attrs_str = '\n'.join('%s [%s]\n' % x
                                  for x in sorted(kwargs['attrs'].items()))
            kwargs['doc'] = ['JSON attributes:\n%s' % attrs_str]
            kwargs['options'] = [
                'null=True'
            ]

    def normalize_field_options(self, kwargs):
        if 'drop' in kwargs:
            return []
        options = kwargs.get('options', [])
        try:
            doc = kwargs['doc']
        except KeyError:
            doc = kwargs['name']
        else:
            if type(doc) is not list:
                kwargs['doc'] = [doc]
        doc = stringify(doc)
        if options and not RE_KWARG.match(options[0]):
            if options[0][0] == '"':
                options[0] = doc
            else:
                for i, o in enumerate(options):
                    if o.startswith('verbose_name='):
                        del options[i]
                        break
                options.append('verbose_name=%s' % doc)
            return [options[0]] + sorted(set(options[1:]))
        return [doc] + sorted(set(options))

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
            kwargs['wrap_options'] = 'null=True' if 'wrap' in kwargs else ''
            if final_django_field == 'models.CharField' and \
                    not any(o.startswith('max_length=') for o in options):
                final_django_field = 'models.TextField'
            if ('null=True' in options and
                ('wrap' in kwargs or
                 final_django_field in ('models.BooleanField',
                                        'models.ManyToManyField'))):
                if final_django_field == 'models.BooleanField':
                    final_django_field = 'models.NullBooleanField'
                options = [o for o in options if o != 'null=True']
            kwargs['options'] = options

            if kwargs.get('coalesce'):
                kwargs['code'] = FIELD_TMPL['_coalesce'] % kwargs
                skip_code = any(('coalesce' in f and
                                 f['coalesce'] == kwargs['coalesce'] and
                                 'code' in f and
                                 ' = ' in f['code'])
                                for f in self.fields)
            else:
                if 'coalesce' in kwargs:
                    del kwargs['coalesce']
                kwargs['code'] = ''

            if not skip_code:
                serialized_options = ', '.join(options)
                tmpl_ctx = dict(kwargs,
                                options0=options[0] if options else None,
                                final_django_field=final_django_field,
                                serialized_options=serialized_options)
                tmpl_row = next((r for r in FIELD_TMPL[tmpl_key].split('\n')
                                 if '%(serialized_options)' in r), None)
                if tmpl_row and len(tmpl_row % tmpl_ctx) > 80:
                    cmt = '# ' if tmpl_row[4] == '#' else ''
                    joiner = ',\n    %s    ' % cmt
                    tmpl_ctx['serialized_options'] = \
                        '\n    %s    %s\n    %s' \
                        % (cmt, joiner.join(options), cmt)
                kwargs['code'] += FIELD_TMPL[tmpl_key] % tmpl_ctx

    def build_code(self):
        model_options = get_opt(self.model_name)

        meta = [template % {'model_lower': self.model_name.lower()}
                for template in (model_options.get('meta', []) +
                                 GLOBAL_MODEL_OPTIONS.get('meta', []))]
        if self.doc and not any(option for option in meta
                                if option.startswith('verbose_name = ')):
            meta.append('verbose_name = %s' % stringify(self.doc))
        if self.abstract and not any(option for option in meta
                                     if option.startswith('abstract = ')):
            meta.append('abstract = True')

        if len(meta):
            meta = '\n\n    class Meta:\n%s' % '\n'.join('        %s' % x
                                                         for x in meta)
        else:
            meta = ''

        methods = '\n\n'.join(model_options.get('methods', ()))
        if methods:
            methods = '\n\n' + methods

        content = ('%(fields)s%(meta)s%(methods)s' % {
                     'fields': '\n'.join([f['code'] for f in self.fields]),
                     'meta': meta,
                     'methods': methods,
                 })
        if not content:
            content = '    pass'

        code = ('# Corresponds to XSD type[s]: %(typename)s\n'
                'class %(name)s(%(parent)s):\n%(content)s\n\n\n' % {
                     'typename': self.type_name,
                     'name': self.model_name,
                     'parent': self.parent or 'models.Model',
                     'content': content,
                 })
        self.code = code

    def add_field(self, **kwargs):
        def fix_related_name(m, django_field, kwargs):
            if django_field in ('models.ManyToManyField', 'models.ForeignKey') \
                    and not any(o.startswith('related_name=')
                                for o in kwargs['options']):
                while m:
                    for f in m.fields:
                        if f.get('django_field') == django_field and \
                               f['options'][0] == kwargs['options'][0] and \
                               f['name'] != kwargs['name']:
                            kwargs['options'].append(
                                'related_name="%s_as_%s"' % (
                                    camelcase_to_underscore(self.model_name),
                                    kwargs['name']
                                )
                            )
                            return
                    m = m.parent_model

        if 'name' in kwargs and match(kwargs['name'],
                                      get_opt(self.model_name, self.type_name),
                                      'drop_after_processing_fields'):
            return

        if 'django_field' in kwargs:
            django_field = kwargs['django_field']

            fix_related_name(self, django_field, kwargs)
            kwargs['django_basefield'] = django_field
            for f in self.builder.fields.values():
                if f['name'] == django_field:
                    kwargs['django_basefield'] = f['parent']
                    break

        self.build_field_code(kwargs)

        self.fields.append(kwargs)

    def add_reverse_field(self,
                          dotted_name=None,
                          one_to_one=False,
                          one_to_many=False,
                          typename=None,
                          name=None,
                          el_def=None):
        assert one_to_one or one_to_many, \
            "add_reverse_field called without one_to_one or one_to_many"

        reverse_name = camelcase_to_underscore(self.model_name)
        fk = {
            'name': reverse_name,
            'options': [
                "'%s'" % self.model_name,
                'on_delete=models.CASCADE',
                'related_name="%s"' % name,
            ],
        }
        if one_to_one:
            fk['django_field'] = 'models.OneToOneField'
            rel, ct2_def = self.builder.get_n_to_one_relation(typename,
                                                              name, el_def)
            kwargs = {'one_to_one': True}
        elif one_to_many:
            fk['django_field'] = 'models.ForeignKey'
            if type(one_to_many) == bool:
                rel, ct2_def = self.builder.get_n_to_many_relation(typename,
                                                                   name, el_def)
            else:
                rel, ct2_def = (one_to_many, None)
            kwargs = {'one_to_many': True}
        self.builder.make_model(rel, ct2_def, add_fields=[fk])
        self.add_field(dotted_name=dotted_name,
                       name=name,
                       doc=[get_doc(el_def, name, self.model_name)],
                       options=[get_model_for_type(rel)],
                       reverse_id_name=reverse_name + "_id",
                       **kwargs)

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


def parse_xmlns(file, ns_map):
    events = "start", "start-ns"
    root = None
    for event, elem in etree.iterparse(file, events):
        if event == "start-ns":
            ns_map.append(elem)
        elif event == "start":
            if root is None:
                root = elem
    return etree.ElementTree(root)


class XSDModelBuilder:

    def __init__(self, infile):
        self.types = set()
        self.models = {}
        self.fields = {}
        self.have_json = False
        ns_map = []
        self.tree = parse_xmlns(infile, ns_map)
        root = self.tree.getroot()
        ns_list = set()
        while len(xpath(self.tree, "//xs:import[@schemaLocation]")):
            for imp in xpath(self.tree, "//xs:import[@schemaLocation]"):
                ns_uri = imp.get('namespace')
                ns = None
                for k, v in ns_map:
                    if v == ns_uri:
                        ns = k + ':'
                        break
                if not ns or ns not in ns_list:
                    loc = imp.get('schemaLocation')
                    subtree = etree.parse(os.path.join(os.path.dirname(infile),
                                                       loc))
                    subroot = subtree.getroot()
                    if ns:
                        for el in subroot:
                            name = el.get('name')
                            if name:
                                el.set('name', ns + name)
                        ns_list.add(ns)
                    root.extend(subroot)
                root.remove(imp)
        self.parent_map = {c: p for p in self.tree.iter() for c in p}
        self.ns_map = dict(ns_map)

    def get_parent_ns(self, el_def):
        root = self.tree.getroot()
        while el_def != root:
            if el_def.tag.endswith(("}complexType", "}simpleType")):
                name = el_def.get('name')
                if name and ':' in name:
                    ns, _ = name.split(':')
                    return ns + ':'
            el_def = self.parent_map[el_def]
        return ''

    def get_min_max(self, parent, restrict_def, validators,):
        def parsedate(d):
            return ['datetime.date(%d, %d, %d)' % (int(d[0:4]), int(d[5:7]),
                                                   int(d[8:10]))]
        min_inclusive = xpath(restrict_def, "xs:minInclusive/@value")
        max_inclusive = xpath(restrict_def, "xs:maxInclusive/@value")
        if parent == 'DateField':
            if min_inclusive:
                min_inclusive = parsedate(min_inclusive[0])
            if max_inclusive:
                max_inclusive = parsedate(max_inclusive[0])
        if min_inclusive:
            validators.append('MinValueValidator(%s)' % min_inclusive[0])
        if max_inclusive:
            validators.append('MaxValueValidator(%s)' % max_inclusive[0])

    def get_max_length(self, options, restrict_def, pattern, enums):
        l = None
        length = (xpath(restrict_def, "xs:length/@value") or
                  xpath(restrict_def, "xs:maxLength/@value"))
        if length:
            l = length[0]
        elif pattern:
            match = re.match(r'\\d\{(\d+,)?(\d+)\}$', pattern)
            if match:
                l = match.group(2)
        if l:
            options['max_length'] = int(l) * \
                    GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor', 1)
        elif enums:
            options['max_length'] = max([len(x) for x in enums])

    def get_digits_options(self, restrict_def, options, parent):
        fraction_digits = xpath(restrict_def, "xs:fractionDigits/@value")
        total_digits = xpath(restrict_def, "xs:totalDigits/@value")
        if fraction_digits:
            options['decimal_places'] = fraction_digits[0]
        if total_digits:
            if parent == 'DecimalField':
                options['max_digits'] = total_digits[0]
            elif parent == 'IntegerField' and int(total_digits[0]) > 9:
                parent = 'BigIntegerField'
        return parent

    def get_field_choices_from_simpletype(self, st_def):
        restrict_def = xpath(st_def, "xs:restriction")[0]
        enumerations = xpath(restrict_def, "xs:enumeration")
        choices = []
        for enumeration in enumerations:
            choices.append((enumeration.get('value'),
                            (get_doc(enumeration, None, None) or
                             enumeration.get('value'))))
        return choices

    def get_field_data_from_simpletype(self, st_def, el_def=None):
        restrict_def = xpath(st_def, "xs:restriction")[0]
        basetype = restrict_def.get("base")
        try:
            doc, parent, options = (get_doc(st_def, None, None),
                                    BASETYPE_FIELD_MAP[basetype],
                                    {})
        except KeyError:
            if ':' not in basetype:
                basetype = self.get_parent_ns(st_def) + basetype
            doc, parent, options = self.get_field_data_from_type(basetype)
        assert type(options) is dict, "options is not a dict"

        pattern = xpath(restrict_def, "xs:pattern/@value")
        enums = xpath(restrict_def, "xs:enumeration/@value")
        min_length = xpath(restrict_def, "xs:minLength/@value")
        validators = []
        self.get_min_max(parent, restrict_def, validators)
        if min_length:
            if min_length[0] == '1':
                options['blank'] = 'False'
            else:
                validators.append('MinLengthValidator(%s)' % min_length[0])
        if pattern:
            pattern = pattern[0]
            validators.append('RegexValidator(r"%s")' % pattern)
        if parent != 'IntegerField':
            self.get_max_length(options, restrict_def, pattern, enums)
        if enums:
            choices = self.get_field_choices_from_simpletype(st_def)
            options['choices'] = \
                '[%s]' % ', '.join('("%s", %s)' % (c[0], stringify(c[1]))
                                   for c in choices)
        parent = self.get_digits_options(restrict_def, options, parent)
        if len(validators):
            options['validators'] = '[%s]' % ', '.join('validators.%s' % x
                                                       for x in validators)
        if parent == 'CharField' and int(options.get('max_length', 1000)) > 500:
            # Some data does not fit, even if XSD says it should
            parent = 'TextField'
        return doc, parent, options

    def get_field_data_from_type(self, typename):
        if typename in TYPE_OVERRIDES:
            return TYPE_OVERRIDES[typename]
        elif typename in BASETYPE_FIELD_MAP:
            return None, None, None
        st_def = xpath(self.tree, "//xs:simpleType[@name=$n]",
                       n=typename)
        if st_def:
            return self.get_field_data_from_simpletype(st_def[0])
        return None, None, None

    def get_field(self, typename, el_def=None, el_path=''):
        if typename not in self.fields:
            if not typename:
                try:
                    st_def = xpath(el_def, "xs:simpleType")[0]
                    doc, parent, options = \
                        self.get_field_data_from_simpletype(st_def, el_def)
                except IndexError:
                    ct_defs = xpath(el_def, "xs:complexType")
                    assert len(ct_defs), (
                        "%s nor a simpleType neither a complexType within %s" %
                        (typename, el_def.get("name"))
                    )

                    self.make_model(el_path, ct_defs[0])
                    model_name = get_model_for_type(el_path)
                    return {
                        'name': 'models.OneToOneField',
                        'options': [model_name, 'on_delete=models.CASCADE'],
                    }
                return {
                    'name': 'models.%s' % parent,
                    'options': ['%s=%s' % (k, v) for k, v in options.items()],
                }
            else:
                if ':' not in typename:
                    typename = self.get_parent_ns(el_def) + typename
                doc, parent, options = self.get_field_data_from_type(typename)
                if parent is None:
                    if typename in BASETYPE_FIELD_MAP:
                        return {
                            'name': 'models.%s' % BASETYPE_FIELD_MAP[typename]
                        }
                    self.make_model(typename)
                    return {
                        'name': 'models.ForeignKey',
                        'options': [get_model_for_type(typename),
                                    'on_delete=models.PROTECT'],
                    }
                if 'choices' in options:
                    st_def = xpath(self.tree, "//xs:simpleType[@name=$n]",
                                   n=typename)[0]
                    choices = self.get_field_choices_from_simpletype(st_def)
                else:
                    choices = None
                self.make_field(typename, doc, parent, options, choices)
        return self.fields[typename]

    def make_field(self, typename, doc, parent, options, choices):
        name = '%sField' \
            % typename.replace(':', '_').replace('.', '_').replace('-', '_')
        code = 'class %(name)s(models.%(parent)s):\n' % {
            'name': name,
            'parent': parent,
        }

        if doc:
            if '\n' in doc:
                code += '    description = (%s)\n\n' % stringify(doc)
            else:
                code += '    description = %s\n\n' % stringify(doc)

        if len(options):
            code += '    def __init__(self, *args, **kwargs):\n' + \
                ''.join('        if "%s" not in kwargs:'
                        ' kwargs["%s"] = %s\n' % (k, k, v)
                        for k, v in options.items()) + \
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

    def simplify_ns(self, typename):
        ns = get_ns(typename)
        if ns and '' in self.ns_map and self.ns_map[ns] == self.ns_map['']:
            return strip_ns(typename)
        return typename

    def get_element_type(self, el_def):
        el_type = el_def.get("type")
        if not el_type:
            try:
                el_type = xpath(el_def, "xs:complexType/xs:complexContent/"
                                "xs:extension[count(*)=0]/@base")[0]
            except IndexError:
                pass
        return self.simplify_ns(el_type)

    def get_element_complex_type(self, el_def):
        el_type = self.get_element_type(el_def)
        if el_type:
            el_type = self.get_parent_ns(el_def) + el_type
            result = xpath(self.tree, "//xs:complexType[@name=$n]", n=el_type)
        else:
            result = xpath(el_def, "xs:complexType")
        try:
            return result[0]
        except IndexError:
            return None

    def get_seq_or_choice(self, parent_def):
        seq_def = xpath(parent_def, "xs:sequence")
        choice_def = xpath(parent_def, "xs:choice")
        return (seq_def[0] if seq_def else None,
                choice_def[0] if choice_def else None)

    def write_seq_or_choice(self, seq_or_choice, typename,
                            prefix='',
                            doc_prefix='',
                            attrs=None,
                            null=False,
                            is_root=False):
        seq_def, choice_def = seq_or_choice
        if choice_def is not None:
            fields = self.models[typename].fields
            n_start = len(fields)
            self.make_fields(typename, choice_def,
                             prefix=prefix,
                             doc_prefix=doc_prefix,
                             attrs=attrs,
                             null=True,
                             is_root=is_root)
            if len(fields) > n_start:
                fields[n_start]['code'] = ('    # xs:choice start\n' +
                                           fields[n_start]['code'])
                fields[-1]['code'] += '\n    # xs:choice end'
        elif seq_def is not None:
            self.make_fields(typename, seq_def,
                             prefix=prefix,
                             doc_prefix=doc_prefix,
                             attrs=attrs,
                             null=null,
                             is_root=is_root)
        return ''

    def write_attributes(self, ct_def, typename,
                         prefix='',
                         doc_prefix='',
                         attrs=None,
                         null=False):
        if ct_def is None:
            return
        attr_defs = xpath(ct_def, "xs:attribute")
        if attr_defs is not None:
            for attr_def in attr_defs:
                attr_name = attr_def.get("name") or attr_def.get("ref")
                dotted_name = '%s@%s' % (prefix, attr_name)
                name = '%s%s' % (prefix.replace('.', '_'), attr_name)
                use_required = (attr_def.get("use") == "required")
                self.make_a_field(typename, name, dotted_name,
                                  attr_def=attr_def,
                                  prefix=prefix,
                                  doc_prefix=doc_prefix,
                                  attrs=attrs,
                                  null=null or not use_required)

    def get_n_to_many_relation(self, typename, name, el_def):
        if el_def.get("maxOccurs") == 'unbounded':
            el2_def = el_def
            el2_name = name
        else:
            try:
                el2_def = xpath(self.get_element_complex_type(el_def),
                                "xs:sequence/xs:element[@maxOccurs=$n]",
                                n='unbounded')[0]
                el2_def = resolve_el_ref(self.tree, el2_def)
                el2_name = '%s_%s' % (name, el2_def.get("name"))
            except IndexError:
                logger.warning("no maxOccurs=unbounded in %s,"
                               " pretending it's unbounded",
                               el_def.get("name"))
                el2_def = el_def
                el2_name = name

        ct2_def = self.get_element_complex_type(el2_def)
        assert ct2_def is not None, \
            "N:many field %s content not a complexType" % name

        rel = ct2_def.get("name") or ('%s.%s' % (typename, el2_name))
        return rel, ct2_def

    def get_n_to_one_relation(self, typename, name, el_def):
        ct2_def = self.get_element_complex_type(el_def)
        assert ct2_def is not None, \
            "N:1 field %s content is not a complexType" % name

        rel = ct2_def.get("name") or ('%s.%s' % (typename, name))
        return rel, ct2_def

    def make_a_field(self, typename, name, dotted_name,
                     el_def=None,
                     attr_def=None,
                     prefix='',
                     doc_prefix='',
                     attrs=None,
                     null=False):
        model_name = get_model_for_type(typename)
        this_model = self.models[typename]
        model = get_opt(model_name, typename)
        el_attr_def = (resolve_attr_ref(self.tree, attr_def) if el_def is None
                       else resolve_el_ref(self.tree, el_def))
        el_type = self.get_element_type(el_attr_def)
        coalesced_dotted_name = dotted_name

        if match(name, model, 'drop_fields'):
            this_model.add_field(dotted_name=dotted_name, drop=True)
            return
        elif model.get('parent_field') == name:
            this_model.add_field(dotted_name=dotted_name, parent_field=True)
            return

        coalesce_target = coalesce(name, model)
        if coalesce_target:
            if name == dotted_name:
                coalesced_dotted_name = coalesce_target
            name = coalesce_target

        doc = get_doc(el_attr_def, name, model_name, doc_prefix=doc_prefix)

        if match(name, model, 'many_to_many_fields'):
            try:
                rel = model.get('many_to_many_field_overrides', {})[name]
                ct2_def = None
            except KeyError:
                rel, ct2_def = self.get_n_to_many_relation(typename, name,
                                                           el_def)
            self.make_model(rel, ct2_def)
            options = [get_model_for_type(rel)]
            override_field_options(name, options, model)
            this_model.add_field(dotted_name=dotted_name,
                                 name=name,
                                 django_field='models.ManyToManyField',
                                 doc=[doc],
                                 options=options)
            return

        elif match(name, model, 'one_to_many_fields'):
            overrides = model.get('one_to_many_field_overrides', {})
            this_model.add_reverse_field(dotted_name=dotted_name,
                                         one_to_many=overrides.get(name, True),
                                         typename=typename,
                                         name=name,
                                         el_def=el_def)
            return

        elif match(name, model, 'one_to_one_fields'):
            this_model.add_reverse_field(dotted_name=dotted_name,
                                         one_to_one=True,
                                         typename=typename,
                                         name=name,
                                         el_def=el_def)
            return

        elif match(name, model, 'json_fields'):
            if not match(name, model, 'drop_after_processing_fields'):
                attrs[coalesced_dotted_name] = doc
            return

        if el_def:
            ct2_def = self.get_element_complex_type(el_def)
            flatten_prefix = name.startswith(cat(o.get('flatten_prefixes', ())
                                                 for o in (GLOBAL_MODEL_OPTIONS,
                                                           model)))
            flatten = match(name, model, 'flatten_fields')
            if (ct2_def is not None and flatten_prefix) or flatten:
                o = {
                    'prefix': '%s.' % dotted_name,
                    'doc_prefix': '%s::' % doc,
                    'attrs': attrs,
                }
                if ct2_def is not None:
                    o['null'] = null or get_null(el_def)
                    ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
                    if not ext2_defs:
                        seq_or_choice2_def = self.get_seq_or_choice(ct2_def)
                        seq_or_choice3_def = (None, None)
                        ct3_def = None
                    else:
                        seq_or_choice2_def = \
                            self.get_seq_or_choice(ext2_defs[0])
                        basetype = ext2_defs[0].get("base")
                        ct3_def = xpath(self.tree, "//xs:complexType[@name=$n]",
                                        n=basetype)[0]
                        seq_or_choice3_def = self.get_seq_or_choice(ct3_def)
                    self.write_attributes(ct3_def, typename, **o)
                    self.write_seq_or_choice(seq_or_choice3_def, typename, **o)
                    self.write_attributes(ct2_def, typename, **o)
                    self.write_seq_or_choice(seq_or_choice2_def, typename, **o)
                    return
                else:
                    logger.warning('complexType not found'
                                   ' while flattening prefix %s',
                                   o['prefix'])

        assert len(name) <= 63, \
            "%s hits PostgreSQL column name 63 char limit!" % name

        basetype = None
        reference_extension = match(name, model, 'reference_extension_fields')
        if reference_extension:
            new_prefix = '%s.' % dotted_name
            assert ct2_def is not None, (
                'complexType not found while processing reference extension'
                ' for prefix %s' % new_prefix
            )
            ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
            try:
                basetype = ext2_defs[0].get("base")
            except IndexError:
                logger.warning("No reference extension while processing prefix"
                               " %s, falling back to normal processing",
                               new_prefix)
                reference_extension = False

        if match(name, model, 'array_fields'):
            assert ct2_def is not None, \
                '%s has no complexType required for array_fields' % dotted_name
            final_el_attr_def = xpath(ct2_def, "xs:sequence/xs:element")[0]
            final_type = self.get_element_type(final_el_attr_def)
            doc = get_doc(final_el_attr_def, name, model_name,
                          doc_prefix=doc + '::')
        else:
            final_el_attr_def = el_attr_def
            final_type = basetype or el_type

        try:
            rel = model.get('foreign_key_overrides', {})[name]
            if rel != '%s.%s' % (typename, name):
                ct2_def = xpath(self.tree, "//xs:complexType[@name=$n]",
                                n=rel)[0]
            else:
                rel, ct2_def = self.get_n_to_one_relation(typename, name,
                                                          el_def)
            self.make_model(rel, ct2_def)
            field = {
                'name': 'models.ForeignKey',
                'options': [get_model_for_type(rel), 'on_delete=models.PROTECT']
            }
        except KeyError:
            field = self.get_field(final_type,
                                   final_el_attr_def,
                                   '%s.%s' % (typename, name))

        choices = field.get('choices', [])
        if any(c[0] not in doc for c in choices):
            doc += '\n' + '\n'.join(
                '%s%s' % (c[0], ' - %s' % c[1] if c[1] != c[0] else '')
                for c in choices
                if '\n%s - ' % c[0] not in doc
            )

        over_class = override_field_class(model_name, typename, name)
        if over_class:
            field = {'name': over_class,
                     'options': field.get('options', [])}

        options = field.get('options', [])

        new_null = null or match(name, model, 'null_fields')
        if new_null:
            if name == model.get('primary_key', None):
                logger.warning("WARNING: %s.%s is a primary key but has"
                               " null=True. Skipping null=True",
                               model_name, name)
            else:
                options.append('null=True')

        default = \
            final_el_attr_def.get('default') or final_el_attr_def.get('fixed')
        if default:
            default = parse_default(final_type, default)
            options.append('default=%s' % repr(default))

        if match(name, model, 'array_fields'):
            field['wrap'] = 'ArrayField'

        if el_def is not None:
            max_occurs = el_def.get("maxOccurs", "1")
            assert \
                (max_occurs == "1") != (field.get('wrap', 0) == "ArrayField"), (
                    "caught maxOccurs=%s in %s.%s (@type=%s). Consider adding"
                    " it to many_to_many_fields, one_to_many_fields,"
                    " array_fields, or json_fields" % (max_occurs, typename,
                                                       name, el_type)
                )
        if name == model.get('primary_key', None):
            options.append('primary_key=True')
            this_model.number_field = name
        elif match(name, model, 'unique_fields'):
            options.append('unique=True')
        elif match(name, model, 'index_fields'):
            options.append('db_index=True')
        override_field_options(name, options, model)

        this_model.add_field(dotted_name=dotted_name,
                             name=name,
                             doc=[doc],
                             django_field=field['name'],
                             options=options,
                             coalesce=coalesce_target,
                             **({'wrap': field['wrap']} if field.get('wrap', 0)
                                else {}))
        if reference_extension:
            seq_or_choice2_def = self.get_seq_or_choice(ext2_defs[0])
            self.write_seq_or_choice(seq_or_choice2_def, typename,
                                     prefix=new_prefix,
                                     doc_prefix=doc_prefix,
                                     attrs=attrs,
                                     null=null)

    def make_fields(self, typename, seq_def,
                    prefix='',
                    doc_prefix='',
                    attrs=None,
                    null=False,
                    is_root=False):
        this_model = self.models[typename]
        null = (null or get_null(seq_def))
        for seq2_def in xpath(seq_def, "xs:sequence"):
            self.write_seq_or_choice((seq2_def, None), typename,
                                     prefix=prefix,
                                     doc_prefix=doc_prefix,
                                     attrs=attrs,
                                     null=null)
        for choice_def in xpath(seq_def, "xs:choice"):
            self.write_seq_or_choice((None, choice_def), typename,
                                     prefix=prefix,
                                     doc_prefix=doc_prefix,
                                     attrs=attrs,
                                     null=null)
        for el_def in xpath(seq_def, "xs:element"):
            el_name = el_def.get("name") or el_def.get("ref")
            dotted_name = prefix + el_name
            name = prefix.replace('.', '_') + el_name

            self.make_a_field(typename, name, dotted_name,
                              el_def=el_def,
                              prefix=prefix,
                              doc_prefix=doc_prefix,
                              attrs=attrs,
                              null=null or get_null(el_def))

        if len(attrs) and is_root:
            this_model.add_field(name='attrs',
                                 django_field='JSONField',
                                 attrs=attrs)
            self.have_json = True

    def make_model(self, typename, ct_def=None, add_fields=None):
        global depth
        depth += 1

        if not get_model_for_type(typename):
            logger.warning('Automatic model name: %s. Consider adding it to'
                           ' TYPE_MODEL_MAP\n',
                           typename)
            TYPE_MODEL_MAP[typename.replace('.', r'\.')] = typename

        if typename in self.types:
            depth -= 1
            return

        self.types.add(typename)

        model_name = get_model_for_type(typename)

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

        parent = None
        deps = []

        if not model.get('custom', False):
            if ct_def is None:
                ct_defs = xpath(self.tree, "//xs:complexType[@name=$n]",
                                n=typename)
                assert ct_defs, "%s not found in schema" % typename
                ct_def = ct_defs[0]

            this_model.abstract = (ct_def.get('abstract') == 'true')

            doc = get_doc(ct_def, None, None)
            if not doc:
                parent_el = self.parent_map[ct_def]
                if parent_el.tag.endswith("element"):
                    doc = get_doc(parent_el, None, None)
            this_model.doc = [doc] if doc else None

            self.write_attributes(ct_def, typename)

            seq_def, choice_def = self.get_seq_or_choice(ct_def)
            if seq_def is None and choice_def is None:
                try:
                    ext_def = xpath(ct_def, "xs:complexContent/xs:extension")[0]
                except IndexError:
                    logger.warning("no sequence/choice and no complexContent"
                                   " in %s complexType",
                                   typename)
                else:
                    try:
                        seq_def = xpath(ext_def, "xs:sequence")[0]
                    except IndexError:
                        assert len(ext_def) == 0, (
                            "no sequence in extension in complexContent in"
                            " %s complexType but %d other children exist"
                            % (typename, len(ext_def))
                        )
                        logger.warning("no additions in extension in"
                                       " complexContent in %s complexType",
                                       typename)
                    parent = self.simplify_ns(ext_def.get("base"))
                    assert parent, (
                        "no base attribute in extension in %s complexType"
                        % typename
                    )
                    if ':' not in parent:
                        parent = self.get_parent_ns(ext_def) + parent

            if not parent:
                parent_field = model.get('parent_field')
                if parent_field:
                    assert seq_def is not None, \
                        'parent_field is set for %s but no sequence' % typename

                    parent = xpath(seq_def, "xs:element[@name=$n]/@type",
                                   n=parent_field)[0]

        if 'parent_type' in model:
            parent = model['parent_type']

        attrs = {}

        if parent:
            if model.get('include_parent_fields'):
                parent_def = xpath(self.tree, "//xs:complexType[@name=$n]",
                                   n=parent)[0]
                self.write_attributes(parent_def, typename)
                self.write_seq_or_choice(self.get_seq_or_choice(parent_def),
                                         typename, attrs=attrs)
                parent = None
            else:
                self.make_model(parent)
                if not this_model.parent_model:
                    this_model.parent_model = self.models[parent]
                parent_model_name = get_model_for_type(parent)
                deps.append(parent_model_name)
                if not this_model.parent:
                    this_model.parent = parent_model_name

        if not model.get('custom', False):
            self.write_seq_or_choice((seq_def, choice_def), typename,
                                     attrs=attrs, is_root=True)

        for f in model.get('add_fields', []) + (add_fields or []):
            if f['django_field'] in ('models.ForeignKey',
                                     'models.ManyToManyField'):
                dep_name = get_a_type_for_model(f['options'][0])
                if dep_name:
                    self.make_model(dep_name)
            this_model.add_field(**f)

        for f in this_model.fields:
            if f.get('django_field') in ('models.ForeignKey',
                                         'models.OneToOneField',
                                         'models.ManyToManyField'):
                if not f['options'][0].startswith("'"):
                    deps.append(f['options'][0])
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
        for typename in typenames:
            if typename.startswith('/'):
                self.make_model('typename1', xpath(self.tree, typename)[0])
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
            for key in sorted(set(attrs1.keys() + attrs2.keys())):
                if key in attrs1 and key in attrs2:
                    attrs[key] = '|'.join(squeeze_docs(cat(a[key].split('|')
                                                           for a in (attrs1,
                                                                     attrs2))))
                else:
                    attrs[key] = attrs1.get(key, attrs2.get(key))
            f1['attrs'] = attrs
            m1.build_field_code(f1, force=True)
            f2['attrs'] = attrs
            m2.build_field_code(f2, force=True)

        def merge_field_docs(model1, field1, model2, field2):
            if 'doc' not in field1 and 'doc' not in field2:
                return
            merged = squeeze_docs(field1['doc'] + field2['doc'])
            if field1['doc'] != merged:
                field1['doc'] = merged
                model1.build_field_code(field1, force=True)
            if field2['doc'] != merged:
                field2['doc'] = merged
                if model2:
                    model2.build_field_code(field2, force=True)

        def merge_field(name, dotted_name, containing_models, models):
            omnipresent = (len(containing_models) == len(models))

            containing_opts = (m.get(dotted_name=dotted_name,
                                     name=name).get('options', [])
                               for m in containing_models)
            if not omnipresent or any('null=True' in o
                                      for o in containing_opts):
                if any('primary_key=True' in o for o in containing_opts):
                    logger.warning("Warning: %s is a primary key but wants"
                                   " null=True in %s",
                                   (name, dotted_name), merged_typename)
                else:
                    for m in containing_models:
                        f = m.get(dotted_name=dotted_name, name=name)
                        if 'options' not in f:
                            f['options'] = []
                        if 'null=True' not in f['options']:
                            f['options'].append('null=True')
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
                    if normalize_code(f['code']) != \
                            normalize_code(first_model_field['code']):
                        force_list = get_opt(m.model_name, m.type_name) \
                            .get('ignore_merge_mismatch_fields', ())
                        assert f.get('dotted_name') in force_list, (
                            "first field in type %s: %s,\n"
                            "second field in type %s: %s"
                            % (containing_models[0].type_name,
                               first_model_field['code'],
                               m.type_name,
                               f['code'])
                        )

            f = first_model_field

            if not omnipresent and not f.get('drop', False):
                if len(containing_models) > len(models) / 2:
                    lacking_models = set(models) - set(containing_models)
                    f['code'] = '    # NULL in %s\n%s' % (
                        ','.join(sorted(m.type_name for m in lacking_models)),
                        f['code'],
                    )
                else:
                    f['code'] = '    # Only in %s\n%s' % (
                        ','.join(sorted(m.type_name
                                        for m in containing_models)),
                        f['code'],
                    )
            return f

        def merge_model_docs(models):
            docs = sorted(set(cat(m.doc for m in models if m.doc)))
            if len(docs) == 0:
                return None
            return docs

        def merge_model_parents(models, merged_models):
            def fix_related_name(m, f):
                old_relname_prefix = 'related_name="%s_as_' \
                    % camelcase_to_underscore(m.model_name)
                for j, option in enumerate(f.get('options', [])):
                    if option.startswith(old_relname_prefix):
                        f['options'][j] = 'related_name="%s_as_%s' \
                            % (camelcase_to_underscore(parents[1]),
                               option[len(old_relname_prefix):])
                        m.build_field_code(f, force=True)
                        break

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

            parents = sorted(set(m.parent for m in models))
            if parents[0] is None and len(parents) == 2:
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
                                check_fields(parent_model, parents[1], m, f, f1)
                                inherited_fields.insert(0, i)
                        for i in inherited_fields:
                            del m.fields[i]
                del parents[0]
            return parents

        def normalize_code(s):
            s = s.replace('..', '.')
            s = re.sub(r'\n?    # xs:choice (start|end)\n?', '', s)
            s = re.sub(r'\n?    # (NULL|Only) in [^\n]+\n', '', s)
            s = re.sub(r'\n?    # [^\n]+ field coalesces to [^\n]+\n', '', s)
            s = re.sub(r'\n?    # The original [^\n]+\n', '', s)
            s = re.sub(r',\s+(#\s+)?related_name="[^"]+"', '', s)
            s = re.sub(r',\s+[a-z_]+=None\b', '', s)
            return s

        def unify_special_cases(field1, field2):
            for f1, f2 in ((field1, field2), (field2, field1)):
                fk_and_one_to_one = (
                    f1.get('django_field') == 'models.OneToOneField' and
                    f2.get('django_field') == 'models.ForeignKey'
                )
                drop_and_add = (f1.get('drop') and not f2.get('drop'))
                if drop_and_add:
                    f2['code'] = \
                        '    # The original %(dotted_name)s is dropped and' \
                        ' replaced by an added one\n%(code)s' % f2
                if fk_and_one_to_one or drop_and_add:
                    f1.clear()
                    f1.update(f2)
                    return

        merged_models = dict()
        merged = dict()
        for model in self.models.itervalues():
            if model.model_name in merged:
                merged[model.model_name].append(model)
            else:
                merged[model.model_name] = [model]
        merged1 = dict()
        merged2 = dict()
        for model_name in merged.keys():
            models = merged[model_name]
            if any(m.parent for m in models):
                merged2[model_name] = models
            else:
                merged1[model_name] = models

        for model_name, models in chain(merged1.iteritems(),
                                        merged2.iteritems()):
            if len(models) == 1:
                merged_model = models[0]
            else:
                merged_typename = '; '.join(sorted(m.type_name for m in models))
                merged_model = Model(self, model_name, merged_typename)

                merged_model.match_fields = models[0].match_fields
                merged_model.number_field = models[0].number_field

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
                                       for f in cat(m.fields for m in models)))
                field_ids = [(f[0], f[2], [m for m in models
                                           if m.get(dotted_name=f[2],
                                                    name=f[0])])
                             for f in field_ids]

                prev = None
                for name, dotted_name, containing_models in field_ids:

                    f = merge_field(name, dotted_name, containing_models,
                                    models)

                    if prev and are_coalesced(prev, f):
                        # The field coalesces with the previous one, so
                        # keep only comments and docs
                        comment_lines = (line for line in f['code'].split('\n')
                                         if line.startswith('    #'))
                        f['code'] = '\n'.join(comment_lines)
                        merge_field_docs(merged_model, prev, None, f)
                    else:
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
            if dep != model.model_name:
                self.write_model(self.models[dep], outfile)
        outfile.write(model.code.encode('utf-8'))
        model.written = True

    def write(self, models_file, fields_file, map_file):
        fields_file.write(HEADER)
        fields_file.write('import datetime\n')
        fields_file.write('from django.core import validators\n')
        fields_file.write('from django.db import models\n\n\n')
        for key in sorted(self.fields):
            field = self.fields[key]
            if 'code' in field:
                fields_file.write(field['code'].encode('utf-8'))

        models_file.write(HEADER)
        models_file.write('import datetime\n')
        models_file.write('from django.core import validators\n')
        models_file.write('from django.db import models\n')
        if self.have_json:
            models_file.write('from django.contrib.postgres.fields import'
                              ' ArrayField, JSONField\n')
        models_file.write('\n')
        if len(self.fields):
            models_file.write(
                'from .fields import \\\n        %s\n'
                % ', \\\n        '.join(sorted(f['name']
                                               for f in self.fields.values()))
            )
        models_file.write(IMPORTS + '\n\n\n')
        for model_name in sorted(self.models.keys()):
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
                if value is not None:
                    model_mapping[key] = value
            mapping[m.model_name] = model_mapping
        json.dump(mapping, map_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    try:
        args = docopt(__doc__)

        builder = XSDModelBuilder(args['<xsd_filename>'])
        builder.make_models([a.decode('UTF-8') for a in args['<xsd_type>']])
        builder.merge_models()
        builder.write(open(args['-m'], "w"),
                      open(args['-f'], "w"),
                      codecs.open(args['-j'], "w", 'utf-8'))
    except Exception as e:
        logger.error('EXCEPTION: %s', unicode(e))
        type, value, tb = sys.exc_info()
        import traceback
        import pdb
        traceback.print_exc()
        pdb.post_mortem(tb)
        sys.exit(1)
