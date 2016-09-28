#! /usr/bin/env python

"""
xsd_to_django_model
Generate Django models from an XSD schema description (and a bunch of hints).

Usage:
    xsd_to_django_model.py [-m <models_filename>] [-f <fields_filename>] [-j <mapping_filename>] <xsd_filename> <xsd_type>...
    xsd_to_django_model.py -h | --help

Options:
    -h --help              Show this screen.
    -m <models_filename>   Output models filename [default: models.py].
    -f <fields_filename>   Output fields filename [default: fields.py].
    -j <mapping_filename>  Output JSON mapping filename [default: mapping.json].
    <xsd_filename>         Input XSD schema filename.
    <xsd_type>             XSD type for which a Django model should be generated.

If you have xsd_to_django_model_settings.py in your PYTHONPATH or in the current directory, it will be imported.
"""


import codecs
from itertools import chain
import json
import re
import sys
import traceback

from docopt import docopt
from lxml import etree


TYPE_MODEL_MAP = {}
MODEL_OPTIONS = {}
GLOBAL_MODEL_OPTIONS = {}
TYPE_OVERRIDES = {}
IMPORTS = ''
try:
    from xsd_to_django_model_settings import *
except ImportError:
    pass

BASETYPE_FIELD_MAP = {
    'xs:boolean': 'BooleanField',
    'xs:byte': 'SmallIntegerField',
    'xs:date': 'DateField',
    'xs:dateTime': 'DateTimeField',
    'xs:decimal': 'DecimalField',
    'xs:double': 'FloatField',
    'xs:int': 'IntegerField',
    'xs:integer': 'IntegerField',
    'xs:long': 'BigIntegerField',
    'xs:positiveInteger': 'PositiveIntegerField',
    'xs:short': 'SmallIntegerField',
    'xs:string': 'CharField',
}
NS = {'xs': "http://www.w3.org/2001/XMLSchema"}

HEADER = '# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT\n# -*- coding: utf-8 -*-\n\nfrom __future__ import unicode_literals\n\n'


def xpath(root, path, **kwargs):
    return root.xpath(path, namespaces=NS, **kwargs)


def get_model_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.iteritems():
        if re.match(expr + '$', name):
            return re.sub(expr + '$', sub, name).replace('+', '')
    return None


def get_merge_for_type(name):
    for expr, sub in TYPE_MODEL_MAP.iteritems():
        if re.match(expr + '$', name):
            return sub.startswith('+')
    return False


def get_doc(el_def, name, model_name):
    name = name or el_def.get('name')
    if model_name:
        try:
            return MODEL_OPTIONS.get(model_name, {})['field_docs'][name]
        except KeyError:
            pass
    doc = xpath(el_def, "xs:annotation/xs:documentation")
    try:
        return doc[0].text.strip().replace('"', '\\"').replace('\n\n', '\n').replace('\n', '\\n"\n"')
    except IndexError:
        return None


def get_null(el_def):
    return el_def.get("minOccurs", None) == "0"


def strip_ns(typename):
    if typename and ':' in typename and not typename.startswith("xs:"):
        _, typename = typename.split(':')
    return typename


def camelcase_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def coalesce(name, model):
    fulldict = dict(model.get('coalesce_fields', {}), **GLOBAL_MODEL_OPTIONS.get('coalesce_fields', {}))
    for expr, sub in fulldict.iteritems():
        match = re.match(expr + '$', name)
        if match:
            return re.sub(expr, sub, name)
    return None


def match(name, model, kind):
    fulltuple = model.get(kind, ()) + GLOBAL_MODEL_OPTIONS.get(kind, ())
    for expr in fulltuple:
        if re.match(expr + '$', name):
            return True
    return False


def override_field_options(field_name, options, model_options):
    add_field_options = dict(model_options.get('field_options', {}), **GLOBAL_MODEL_OPTIONS.get('field_options', {}))
    if field_name in add_field_options:
        for option in add_field_options[field_name]:
            option_key, _ = option.split('=')
            for n, old_option in enumerate(options):
                if old_option.split('=')[0] == option_key:
                    del options[n]
                    break
        options += add_field_options[field_name]


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

    def build_field_code(self, kwargs, force=False):
        if kwargs.get('name') == 'attrs':
            kwargs['options'] = ['"JSON attributes:\\n"\n%s' % '\n'.join(['"%s [%s]\\n"' % x for x in sorted(kwargs['attrs'].items())]), 'null=True']

        skip_code = False
        if force or 'code' not in kwargs:
            if kwargs.get('drop', False):
                template = '    # Dropping %(dotted_name)s field'
            elif kwargs.get('parent_field', False):
                template = '    # %(dotted_name)s field translates to this model\'s parent'
            elif 'one_to_many' in kwargs:
                template = ('    # %(name)s is declared as a reverse relation from %(options0)s\n'
                            '    # %(name)s = OneToManyField(%(serialized_options)s)')
            elif 'one_to_one' in kwargs:
                template = ('    # %(name)s is declared as a reverse relation from %(options0)s\n'
                            '    # %(name)s = OneToOneField(%(serialized_options)s)')
            else:
                template = '    %(name)s = %(final_django_field)s(%(serialized_options)s)'

            final_django_field = kwargs.get('django_field')
            try:
                options = kwargs['options']
                if len(options):
                    if '=' not in options[0]:
                        options = [options[0]] + sorted(set(options[1:]))
                    else:
                        options = sorted(set(options))
            except KeyError:
                options = []
            serialized_options = ', '.join(options)
            if 'null=True' in kwargs.get('options', []):
                if final_django_field in ('models.BooleanField', 'models.ManyToManyField'):
                    if final_django_field == 'models.BooleanField':
                        final_django_field = 'models.NullBooleanField'
                    serialized_options = ', '.join(o for o in options if o != 'null=True')

            if kwargs.get('coalesce'):
                kwargs['code'] = '    # %(dotted_name)s field coalesces to %(coalesce)s\n' % kwargs
                for f in self.fields:
                    if 'coalesce' in f and f['coalesce'] == kwargs['coalesce'] and 'code' in f and ' = ' in f['code']:
                        skip_code = True
                        break
            else:
                if 'coalesce' in kwargs:
                    del kwargs['coalesce']
                kwargs['code'] = ''

            if not skip_code:
                kwargs['code'] += template % dict(kwargs,
                                                  options0=kwargs['options'][0] if kwargs.get('options') else '',
                                                  final_django_field=final_django_field,
                                                  serialized_options=serialized_options)

    def build_code(self):
        model_options = MODEL_OPTIONS.get(self.model_name, {})

        meta = [template % {'model_lower': self.model_name.lower()}
                for template in model_options.get('meta', []) + GLOBAL_MODEL_OPTIONS.get('meta', [])]
        if self.doc and not any(option for option in meta if option.startswith('verbose_name = ')):
            meta.append('verbose_name = "%s"' % self.doc)
        if len(meta):
            meta = '\n\n    class Meta:\n%s' % '\n'.join('        %s' % x for x in meta)
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

        code = ('# Corresponds to XSD type[s]: %(typename)s\nclass %(name)s(%(parent)s):\n%(content)s\n\n' % {
                     'typename': self.type_name,
                     'name': self.model_name,
                     'parent': self.parent or 'models.Model',
                     'content': content,
                 })
        self.code = code

    def add_field(self, **kwargs):
        def fix_related_name(m, django_field, kwargs):
            if django_field in ('models.ManyToManyField', 'models.ForeignKey'):
                while m:
                    for f in m.fields:
                        if f.get('django_field') == django_field:
                            if f['options'][0] == kwargs['options'][0]:
                                if f['name'] != kwargs['name']:
                                    kwargs['options'].append('related_name="%s_as_%s"' % (camelcase_to_underscore(self.model_name), kwargs['name']))
                                    return
                    m = m.parent_model

        if 'name' in kwargs and match(kwargs['name'], MODEL_OPTIONS.get(self.model_name, {}), 'drop_after_processing_fields'):
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

    def add_reverse_field(self, dotted_name=None, one_to_one=False, one_to_many=False, typename=None, name=None, el_def=None):
        reverse_name = camelcase_to_underscore(self.model_name)
        fk = {
            'name': reverse_name,
            'options': ['"%s"' % self.model_name, 'on_delete=models.CASCADE', 'related_name="%s"' % name],
        }
        if one_to_one:
            fk['django_field'] = 'models.OneToOneField'
            rel, ct2_def = self.builder.get_n_to_one_relation(typename, name, el_def)
            kwargs = {'one_to_one': True}
        elif one_to_many:
            fk['django_field'] = 'models.ForeignKey'
            if type(one_to_many) == bool:
                rel, ct2_def = self.builder.get_n_to_many_relation(typename, name, el_def)
            else:
                rel, ct2_def = (one_to_many, None)
            kwargs = {'one_to_many': True}
        else:
            raise Exception("add_reverse_field called without one_to_one or one_to_many")
        self.builder.make_model(rel, ct2_def, add_fields=[fk])
        self.add_field(dotted_name=dotted_name, name=name,
                       options=[get_model_for_type(rel), 'verbose_name="%s"' % get_doc(el_def, name, self.model_name)],
                       reverse_id_name=reverse_name + "_id", **kwargs)

    def get(self, dotted_name=None, name=None):
        if dotted_name and name:
            for f in self.fields:
                if f.get('dotted_name') == dotted_name and f.get('name') == name:
                    return f
        else:
            for f in self.fields:
                if dotted_name and f.get('dotted_name') == dotted_name:
                    return f
                elif name and f.get('name') == name:
                    return f
        return None


class XSDModelBuilder:
    def __init__(self, infile):
        self.types = set()
        self.models = {}
        self.fields = {}
        self.tree = etree.parse(infile)
        self.have_json = False


    def get_field_data_from_simpletype(self, st_def):
        restrict_def = xpath(st_def, "xs:restriction")[0]
        basetype = restrict_def.get("base")
        try:
            parent = BASETYPE_FIELD_MAP[basetype]
        except KeyError:
            return self.get_field_data_from_type(basetype)

        length = xpath(restrict_def, "xs:length/@value") or xpath(restrict_def, "xs:maxLength/@value")
        pattern = xpath(restrict_def, "xs:pattern/@value")
        enums = xpath(restrict_def, "xs:enumeration/@value")
        min_length = xpath(restrict_def, "xs:minLength/@value")
        fraction_digits = xpath(restrict_def, "xs:fractionDigits/@value")
        total_digits = xpath(restrict_def, "xs:totalDigits/@value")
        min_inclusive = xpath(restrict_def, "xs:minInclusive/@value")
        max_inclusive = xpath(restrict_def, "xs:maxInclusive/@value")
        options = {}
        validators = []
        if length:
            options['max_length'] = int(length[0]) * GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor', 1)
        if min_length:
            if min_length[0] == '1':
                options['blank'] = 'False'
            else:
                validators.append('MinLengthValidator(%s)' % min_length[0])
        if min_inclusive:
            validators.append('MinValueValidator(%s)' % min_inclusive[0])
        if max_inclusive:
            validators.append('MaxValueValidator(%s)' % max_inclusive[0])
        if pattern:
            pattern = pattern[0]
            validators.append('RegexValidator(r"%s")' % pattern)
            match = re.match(r'\\d\{(\d+,)?(\d+)\}$', pattern)
            if match and 'max_length' not in options:
                options['max_length'] = int(match.group(2)) * GLOBAL_MODEL_OPTIONS.get('charfield_max_length_factor', 1)
        if enums:
            if 'max_length' not in options:
                options['max_length'] = max([len(x) for x in enums])
            options['choices'] = '[%s]' % ', '.join(['("%s", "%s")' % (x, x) for x in enums])
        if fraction_digits:
            options['decimal_places'] = fraction_digits[0]
        if total_digits:
            options['max_digits'] = total_digits[0]
        if len(validators):
            options['validators'] = '[%s]' % ', '.join(['validators.%s' % x for x in validators])
        doc = get_doc(st_def, None, None)
        if parent == 'IntegerField' and 'max_length' in options:
            del options['max_length']
        if parent == 'CharField' and int(options.get('max_length', 1000)) > 500:
            # Some data does not fit, even if XSD says it should
            parent = 'TextField'
        return doc, '%s' % parent, options

    def get_field_data_from_type(self, typename):
        if typename in TYPE_OVERRIDES:
            return TYPE_OVERRIDES[typename]
        elif typename in BASETYPE_FIELD_MAP:
            return None, None, None
        st_def = xpath(self.tree, "//xs:simpleType[@name=$n]", n=typename)
        if st_def:
            return self.get_field_data_from_simpletype(st_def[0])
        return None, None, None

    def get_field(self, typename, el_def=None, el_path=''):
        if typename not in self.fields:
            if not typename:
                try:
                    st_def = xpath(el_def, "xs:simpleType")[0]
                    doc, parent, options = self.get_field_data_from_simpletype(st_def)
                except IndexError:
                    try:
                        ct_def = xpath(el_def, "xs:complexType")[0]
                    except IndexError:
                        raise Exception("%s nor a simpleType neither a complexType within %s" % (typename, el_def.get("name")))
                    self.make_model(el_path, ct_def)
                    model_name = get_model_for_type(el_path)
                    return {'name': 'models.OneToOneField', 'options': [model_name, 'on_delete=models.CASCADE']}
                return {
                    'name': 'models.%s' % parent,
                    'options': ['%s=%s' % (k, v) for k, v in options.items()],
                }
            else:
                doc, parent, options = self.get_field_data_from_type(typename)
                if parent is None:
                    if typename in BASETYPE_FIELD_MAP:
                        return {'name': 'models.%s' % BASETYPE_FIELD_MAP[typename]}
                    self.make_model(typename)
                    return {'name': 'models.ForeignKey', 'options': [get_model_for_type(typename), 'on_delete=models.PROTECT']}
                self.make_field(typename, doc, parent, options)
        return self.fields[typename]

    def make_field(self, typename, doc, parent, options):
        name = '%sField' % typename.replace('.', '_')
        code = 'class %(name)s(models.%(parent)s):\n' % {'name': name, 'parent': parent}

        if doc:
            if '\n' in doc:
                code += '    description = ("%s")\n\n' % doc
            else:
                code += '    description = "%s"\n\n' % doc

        if len(options):
            code += '    def __init__(self, *args, **kwargs):\n'
            for k, v in options.items():
                code += '        if "%s" not in kwargs: kwargs["%s"] = %s\n' % (k, k, v)
            code += '        super(%s, self).__init__(*args, **kwargs)\n\n' % name
        if not doc and not len(options):
            code += '    # SOMETHING STRANGE\n    pass\n'

        code += '\n'
        self.fields[typename] = {
            'code': code,
            'name': name,
            'parent': 'models.%s' % parent,
        }

    def get_element_type(self, el_def):
        el_type = el_def.get("type")
        if not el_type:
            try:
                el_type = xpath(el_def, "xs:complexType/xs:complexContent/xs:extension[count(*)=0]/@base")[0]
            except IndexError:
                pass
        if el_type:
            el_type = strip_ns(el_type)
        return el_type

    def get_element_complex_type(self, el_def):
        el_type = self.get_element_type(el_def)
        if el_type:
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
        return seq_def[0] if seq_def else None, choice_def[0] if choice_def else None

    def write_seq_or_choice(self, seq_or_choice, typename, prefix='', attrs=None, null=False, is_root=False):
        seq_def, choice_def = seq_or_choice
        if choice_def is not None:
            fields = self.models[typename].fields
            n_start = len(fields)
            self.make_fields(typename, choice_def, prefix=prefix, attrs=attrs, null=True, is_root=is_root)
            if len(fields) > n_start:
                fields[n_start]['code'] = '    # xs:choice start\n' + fields[n_start]['code']
                fields[-1]['code'] += '\n    # xs:choice end'
        elif seq_def is not None:
            self.make_fields(typename, seq_def, prefix=prefix, attrs=attrs, null=null, is_root=is_root)
        return ''

    def write_attributes(self, ct_def, typename):
        attr_defs = xpath(ct_def, "xs:attribute")
        if attr_defs is not None:
            model_name = get_model_for_type(typename)
            this_model = self.models[typename]
            model = MODEL_OPTIONS.get(model_name, {})
            for attr_def in attr_defs:
                attr_name = attr_def.get("name")
                field = self.get_field(attr_def.get("type"))
                options = field.get('options', [])
                doc = get_doc(attr_def, None, model_name)
                options[:0] = ['"%s"' % doc]
                if attr_def.get("use") == "required":
                    options.append('null=True')
                override_field_options(attr_name, options, model)
                this_model.add_field(dotted_name="@%s" % attr_name, name=attr_name, django_field=field['name'], options=options)

    def get_n_to_many_relation(self, typename, name, el_def):
        if el_def.get("maxOccurs") == 'unbounded':
            el2_def = el_def
            el2_name = name
        else:
            try:
                el2_def = xpath(self.get_element_complex_type(el_def), "xs:sequence/xs:element[@maxOccurs=$n]", n='unbounded')[0]
                el2_name = '%s_%s' % (name, el2_def.get("name"))
            except IndexError as e:
                print "no maxOccurs=unbounded in %s, pretending it's unbounded" % el_def.get("name")
                el2_def = el_def
                el2_name = name
        ct2_def = self.get_element_complex_type(el2_def)
        if ct2_def is None:
            raise Exception("N_to_many field %s content is not a complexType\n" % name)
        rel = ct2_def.get("name") or ('%s.%s' % (typename, el2_name))
        return rel, ct2_def

    def get_n_to_one_relation(self, typename, name, el_def):
        ct2_def = self.get_element_complex_type(el_def)
        if ct2_def is None:
            raise Exception("n_to_one field %s content is not a complexType\n" % name)
        rel = ct2_def.get("name") or ('%s.%s' % (typename, name))
        return rel, ct2_def

    def make_fields(self, typename, seq_def, prefix='', attrs=None, null=False, is_root=False):
        model_name = get_model_for_type(typename)
        this_model = self.models[typename]
        model = MODEL_OPTIONS.get(model_name, {})
        for choice_def in xpath(seq_def, "xs:choice"):
            self.write_seq_or_choice((None, choice_def), typename, prefix=prefix, attrs=attrs, null=null)
        for el_def in xpath(seq_def, "xs:element"):
            el_name = el_def.get("name")
            dotted_name = prefix + el_name
            coalesced_dotted_name = dotted_name
            name = dotted_name.replace('.', '_')
            el_type = self.get_element_type(el_def)

            if match(name, model, 'drop_fields'):
                this_model.add_field(dotted_name=dotted_name, drop=True)
                continue
            elif model.get('parent_field') == name:
                this_model.add_field(dotted_name=dotted_name, parent_field=True)
                continue

            coalesce_target = coalesce(name, model)
            if coalesce_target:
                if name == dotted_name:
                    coalesced_dotted_name = coalesce_target
                name = coalesce_target

            if match(name, model, 'many_to_many_fields'):
                try:
                    rel = model.get('many_to_many_field_overrides', {})[name]
                    ct2_def = None
                except KeyError:
                    rel, ct2_def = self.get_n_to_many_relation(typename, name, el_def)
                self.make_model(rel, ct2_def)
                this_model.add_field(dotted_name=dotted_name, name=name, django_field='models.ManyToManyField', options=[get_model_for_type(rel), 'verbose_name="%s"' % get_doc(el_def, name, model_name)])
                continue

            elif match(name, model, 'one_to_many_fields'):
                this_model.add_reverse_field(dotted_name=dotted_name, one_to_many=model.get('one_to_many_field_overrides', {}).get(name, True), typename=typename, name=name, el_def=el_def)
                continue

            elif match(name, model, 'one_to_one_fields'):
                this_model.add_reverse_field(dotted_name=dotted_name, one_to_one=True, typename=typename, name=name, el_def=el_def)
                continue

            elif match(name, model, 'json_fields'):
                if not match(name, model, 'drop_after_processing_fields'):
                    attrs[coalesced_dotted_name] = get_doc(el_def, name, model_name)
                continue

            ct2_def = self.get_element_complex_type(el_def)
            flatten_prefix = name.startswith(GLOBAL_MODEL_OPTIONS.get('flatten_prefixes', ()) +
                                             model.get('flatten_prefixes', ()))
            flatten = match(name, model, 'flatten_fields')
            if (ct2_def is not None and flatten_prefix) or flatten:
                new_prefix = '%s.' % dotted_name
                if ct2_def is None:
                    raise Exception('complexType not found while flattening prefix %s' % new_prefix)
                new_null = null or get_null(el_def)
                ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
                if not ext2_defs:
                    seq_or_choice2_def = self.get_seq_or_choice(ct2_def)
                    seq_or_choice3_def = (None, None)
                else:
                    seq_or_choice2_def = self.get_seq_or_choice(ext2_defs[0])
                    basetype = ext2_defs[0].get("base")
                    ct3_def = xpath(self.tree, "//xs:complexType[@name=$n]", n=basetype)[0]
                    seq_or_choice3_def = self.get_seq_or_choice(ct3_def)
                fields = this_model.fields
                old_len = len(fields)
                self.write_seq_or_choice(seq_or_choice3_def, typename, prefix=new_prefix, attrs=attrs, null=new_null)
                self.write_seq_or_choice(seq_or_choice2_def, typename, prefix=new_prefix, attrs=attrs, null=new_null)
                #if len(fields) == old_len:
                #    raise Exception('    # SOMETHING STRANGE - flatten_fields RENDER VOID FOR %s\n' % new_prefix)
                continue

            if len(name) > 63:
                raise Exception("%s hits PostgreSQL 63 chars column name limit!" % name)

            basetype = None
            reference_extension = match(name, model, 'reference_extension_fields')
            if reference_extension:
                new_prefix = '%s.' % dotted_name
                if ct2_def is None:
                    raise Exception('complexType not found while processing reference extension for prefix %s' % new_prefix)
                ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
                try:
                    basetype = ext2_defs[0].get("base")
                except IndexError:
                    print "No reference extension while processing prefix %s, falling back to normal processing" % new_prefix
                    reference_extension = False

            try:
                rel = model.get('foreign_key_overrides', {})[name]
                if rel != '%s.%s' % (typename, name):
                    ct2_def = xpath(self.tree, "//xs:complexType[@name=$n]", n=rel)[0]
                else:
                    rel, ct2_def = self.get_n_to_one_relation(typename, name, el_def)
                self.make_model(rel, ct2_def)
                field = {'name': 'models.ForeignKey', 'options': [get_model_for_type(rel), 'on_delete=models.PROTECT']}
            except KeyError:
                field = self.get_field(basetype or el_type, el_def, '%s.%s' % (typename, name))

            try:
                field = {'name': model.get('override_field_class', {})[name],
                         'options': field.get('options', [])}
            except KeyError:
                pass

            options = field.get('options', [])
            doc = get_doc(el_def, name, model_name)
            if doc:
                if field['name'] in ('models.ForeignKey', 'models.OneToOneField'):
                    options.append('verbose_name="%s"' % doc)
                else:
                    options[:0] = ['"%s"' % doc]

            new_null = null or get_null(el_def) or match(name, model, 'null_fields')
            if new_null:
                if name == model.get('primary_key', None):
                    print "WARNING: %s.%s is a primary key but has null=True. Skipping null=True" % (model_name, name)
                else:
                    options.append('null=True')
            max_occurs = el_def.get("maxOccurs", None)
            if max_occurs:
                raise Exception("caught maxOccurs=%s in %s.%s (@type=%s). Consider adding it to many_to_many_fields, one_to_many_fields or json_fields" % (max_occurs, typename, name, el_type))
            if name == model.get('primary_key', None):
                options.append('primary_key=True')
                this_model.number_field = name
            elif match(name, model, 'unique_fields'):
                options.append('unique=True')
            elif match(name, model, 'index_fields'):
                options.append('db_index=True')
            override_field_options(name, options, model)

            this_model.add_field(dotted_name=dotted_name, name=name, django_field=field['name'], options=options, coalesce=coalesce_target)
            if reference_extension:
                seq_or_choice2_def = self.get_seq_or_choice(ext2_defs[0])
                self.write_seq_or_choice(seq_or_choice2_def, typename, prefix=new_prefix, attrs=attrs, null=null)
        if len(attrs) and is_root:
            this_model.add_field(name='attrs', django_field='JSONField', attrs=attrs)
            self.have_json = True

    def make_model(self, typename, ct_def=None, add_fields=None):
        typename = strip_ns(typename)

        if not get_model_for_type(typename):
            TYPE_MODEL_MAP[typename.replace('.', r'\.')] = typename
            sys.stderr.write('Automatic model name: %s. Consider adding it to TYPE_MODEL_MAP\n' % typename)

        if typename in self.types:
            return

        self.types.add(typename)

        model_name = get_model_for_type(typename)

        model = MODEL_OPTIONS.get(model_name, {})

        sys.stderr.write('Making model for type %s\n' % typename)

        if typename not in self.models:
            this_model = Model(self, model_name, typename)
            self.models[typename] = this_model
        ### MERGE PROCESSING
        elif not get_merge_for_type(typename):
            raise Exception("Not merging type %s, model %s already exists and no merge (+) prefix specified" % (typename, model_name))

        parent = None
        deps = []

        if not model.get('custom', False):
            if ct_def is None:
                ct_defs = xpath(self.tree, "//xs:complexType[@name=$n]", n=typename)
                if not ct_defs:
                    raise Exception("%s not found in schema" % typename)
                ct_def = ct_defs[0]

            doc = get_doc(ct_def, None, None)
            this_model.doc = doc

            fields = ''

            self.write_attributes(ct_def, typename)

            seq_def, choice_def = self.get_seq_or_choice(ct_def)
            if seq_def is None and choice_def is None:
                try:
                    ext_def = xpath(ct_def, "xs:complexContent/xs:extension")[0]
                except IndexError:
                    raise Exception("no sequence/choice and no complexContent in %s complexType" % typename)
                try:
                    seq_def = xpath(ext_def, "xs:sequence")[0]
                except IndexError:
                    if len(ext_def) == 0:
                        sys.stderr.write("WARNING: no additions in extension in complexContent in %s complexType\n" % typename)
                    else:
                        raise Exception("no sequence in extension in complexContent in %s complexType but %d other children exist" % (typename, len(ext_def)))
                parent = ext_def.get("base")
                if not parent:
                    raise Exception("no base attribute in extension in %s complexType" % typename)

            if not parent:
                parent_field = model.get('parent_field')
                if parent_field:
                    if seq_def is None:
                        raise Exception('parent_field is set for %s but no sequence' % typename)
                    parent = xpath(seq_def, "xs:element[@name=$n]/@type", n=parent_field)[0]

        if 'parent_type' in model:
            parent = model['parent_type']

        attrs = {}

        if parent:
            if model.get('include_parent_fields'):
                parent_def = xpath(self.tree, "//xs:complexType[@name=$n]", n=strip_ns(parent))[0]
                self.write_attributes(parent_def, typename)
                self.write_seq_or_choice(self.get_seq_or_choice(parent_def), typename, attrs=attrs)
                parent = None
            else:
                stripped_parent = strip_ns(parent)
                self.make_model(stripped_parent)
                if not this_model.parent_model:
                    this_model.parent_model = self.models[stripped_parent]
                parent_model_name = get_model_for_type(stripped_parent)
                deps.append(parent_model_name)
                if not this_model.parent:
                    this_model.parent = parent_model_name

        if not model.get('custom', False):
            self.write_seq_or_choice((seq_def, choice_def), typename, attrs=attrs, is_root=True)

        for f in model.get('add_fields', []) + (add_fields or []):
            this_model.add_field(**f)

        for f in this_model.fields:
            if f.get('django_field') in ('models.ForeignKey', 'models.OneToOneField', 'models.ManyToManyField'):
                if not f['options'][0].startswith('"'):
                    deps.append(f['options'][0])
        this_model.deps = list(set(deps + (this_model.deps or [])))

        if not this_model.number_field:
            try:
                this_model.number_field = model['number_field']
            except KeyError:
                if this_model.parent_model:
                    this_model.number_field = this_model.parent_model.number_field

        this_model.build_code()

        if 'match_fields' in model:
            this_model.match_fields = model['match_fields']

        sys.stderr.write('Done making model %s (%s)\n' % (model_name, typename))

    def make_models(self, typenames):
        for typename in typenames:
            self.make_model(typename)

    def merge_models(self):
        def merge_attrs(m1, f1, m2, f2):
            attrs1 = f1['attrs']
            attrs2 = f2['attrs']
            attrs = {}
            for key in sorted(set(attrs1.keys() + attrs2.keys())):
                if key in attrs1 and key in attrs2:
                    attrs[key] = '|'.join(sorted(set(attrs1[key].split('|') + attrs2[key].split('|'))))
                else:
                    attrs[key] = attrs1.get(key, attrs2.get(key))
            f1['attrs'] = attrs
            m1.build_field_code(f1, force=True)
            f2['attrs'] = attrs
            m2.build_field_code(f2, force=True)

        def merge_model_docs(models):
            docs = sorted(set(m.doc for m in models if m.doc))
            if len(docs) == 0:
                return None
            if len(docs) == 1:
                return docs[0]
            return ' | '.join(m.doc for m in models if m.doc)

        def merge_model_parents(models, merged_models):
            parents = sorted(set(m.parent for m in models))
            if parents[0] is None and len(parents) == 2:
                parent_model = merged_models[parents[1]]
                for m in models:
                    if m.parent is None:
                        inherited_fields = []
                        for i, f in enumerate(m.fields):
                            f1 = parent_model.get(dotted_name=f.get('dotted_name'), name=f.get('name'))
                            if f1:
                                if f1.get('name') == 'attrs':
                                    merge_attrs(parent_model, f1, m, f)
                                old_relname_prefix = 'related_name="%s_as_' % camelcase_to_underscore(m.model_name)
                                for j, option in enumerate(f.get('options', [])):
                                    if option.startswith(old_relname_prefix):
                                        f['options'][j] = 'related_name="%s_as_%s' % (camelcase_to_underscore(parents[1]), option[len(old_relname_prefix):])
                                        m.build_field_code(f, force=True)
                                        break
                                if normalize_code(f1['code']) == normalize_code(f['code']) or (f1.get('dotted_name') in MODEL_OPTIONS.get(parent_model.model_name, {}).get('ignore_merge_mismatch_fields', ())):
                                    inherited_fields.insert(0, i)
                                else:
                                    raise Exception('different field code while merging %s: %s; %s: %s' % (parents[1], f1['code'], m.model_name, f['code']))
                        for i in inherited_fields:
                            del m.fields[i]
                del parents[0]
            return parents

        def normalize_code(s):
            s = s.replace('..', '.')
            s = re.sub(r'\n?    # xs:choice (start|end)\n?', '', s)
            s = re.sub(r'\n?    # (NULL|Only) in [^\n]+\n', '', s)
            s = re.sub(r'\n?    # [^\n]+ field coalesces to [^\n]+\n', '', s)
            s = re.sub(r', related_name="[^"]+"', '', s)
            return s

        def unify_one_to_one_and_fk(field1, field2):
            for f1, f2 in ((field1, field2), (field2, field1)):
                if f1['django_field'] == 'models.OneToOneField' and f2['django_field'] == 'models.ForeignKey':
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

        for model_name, models in chain(merged1.iteritems(), merged2.iteritems()):
            if len(models) == 1:
                merged_model = models[0]
            else:
                merged_typename = '; '.join(sorted(m.type_name for m in models))
                merged_model = Model(self, model_name, merged_typename)

                merged_model.match_fields = models[0].match_fields
                merged_model.number_field = models[0].number_field

                parents = merge_model_parents(models, merged_models)
                if len(parents) > 1:
                    raise Exception("different parents %s for types %s" % (parents, merged_typename))
                elif len(parents):
                    merged_model.parent = parents[0]

                merged_model.deps = sorted(set(chain(*[m.deps for m in models if m.deps])))

                field_ids = sorted(set((f.get('coalesce', f.get('name')),
                                        #None if 'coalesce' in f else f.get('dotted_name'))
                                        f.get('dotted_name'))
                                       for f in chain(*[m.fields for m in models])))
                field_ids = [(f[0], f[1], [m for m in models if m.get(dotted_name=f[1], name=f[0])])
                             for f in field_ids]

                for name, dotted_name, containing_models in field_ids:
                    omnipresent = (len(containing_models) == len(models))

                    if not omnipresent or any('null=True' in m.get(dotted_name=dotted_name, name=name).get('options', [])
                                              for m in containing_models):
                        if any('primary_key=True' in m.get(dotted_name=dotted_name, name=name).get('options', [])
                               for m in containing_models):
                            print "Warning: %s is a primary key but wants null=True in %s" % ((name, dotted_name), merged_typename)
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
                        else:
                            if 'name' in f and f['name'] == 'attrs':
                                merge_attrs(containing_models[0], first_model_field, m, f)
                            elif 'django_field' in f:
                                unify_one_to_one_and_fk(f, first_model_field)
                            if normalize_code(f['code']) != normalize_code(first_model_field['code']):
                                if f.get('dotted_name') not in MODEL_OPTIONS.get(m.model_name, {}).get('ignore_merge_mismatch_fields', ()):
                                    raise Exception("first field in type %s: %s, second field in type %s: %s" % (containing_models[0].type_name, first_model_field['code'], m.type_name, f['code']))

                    f = first_model_field

                    if len(merged_model.fields) and 'coalesce' in f and merged_model.fields[-1].get('coalesce') == f['coalesce']:
                        # The field coalesces with the previous one, so keep only comments
                        f['code'] = '\n'.join(line for line in f['code'].split('\n') if line.startswith('    #'))

                    if not omnipresent and not f.get('drop', False):
                        if len(containing_models) > len(models) / 2:
                            f['code'] = '    # NULL in %s\n%s' % (','.join(sorted(m.type_name for m in set(models) - set(containing_models))), f['code'])
                        else:
                            f['code'] = '    # Only in %s\n%s' % (','.join(sorted(m.type_name for m in containing_models)), f['code'])

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
        fields_file.write('from django.core import validators\n')
        fields_file.write('from django.db import models\n\n\n')
        for key in sorted(self.fields):
            field = self.fields[key]
            if 'code' in field:
                fields_file.write(field['code'].encode('utf-8'))

        models_file.write(HEADER)
        models_file.write('from django.core import validators\n')
        models_file.write('from django.db import models\n')
        if self.have_json:
            models_file.write('from django.contrib.postgres.fields import JSONField\n')
        models_file.write('\n')
        if len(self.fields):
            models_file.write('from .fields import %s\n' % ', '.join(sorted(f['name'] for f in self.fields.values())))
        models_file.write(IMPORTS + '\n\n\n')
        for model_name in sorted(self.models.keys()):
            self.write_model(self.models[model_name], models_file)

        mapping = {}
        for m in self.models.values():
            model_mapping = {}
            for key in ('model_name', 'fields', 'parent', 'match_fields', 'number_field'):
                value = getattr(m, key)
                if value is not None:
                    model_mapping[key] = value
            mapping[m.model_name] = model_mapping
        json.dump(mapping, map_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    try:
        args = docopt(__doc__)

        builder = XSDModelBuilder(args['<xsd_filename>'])
        builder.make_models(args['<xsd_type>'])
        builder.merge_models()
        builder.write(open(args['-m'], "w"),
                      open(args['-f'], "w"),
                      codecs.open(args['-j'], "w", 'utf-8'))
    except Exception as e:
        print 'EXCEPTION: ' + unicode(e).encode('utf-8')
        traceback.print_exc()
        sys.exit(1)
