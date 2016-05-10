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
from docopt import docopt
import json
import re
import sys

from lxml import etree


TYPE_MODEL_MAP = {}
MODEL_OPTIONS = {}
GLOBAL_MODEL_OPTIONS = {}
TYPE_OVERRIDES = {}
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
    'xs:string': 'CharField',
}
NS = {'xs': "http://www.w3.org/2001/XMLSchema"}

HEADER = '# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT\n# -*- coding: utf-8 -*-\n\nfrom __future__ import unicode_literals\n\n'


def xpath(root, path, **kwargs):
    return root.xpath(path, namespaces=NS, **kwargs)


def get_model_for_type(name):
    for expr, model in TYPE_MODEL_MAP.iteritems():
        if re.match(expr + '$', name):
            return model
    return None


def get_doc(el_def):
    doc = xpath(el_def, "xs:annotation/xs:documentation")
    try:
        return doc[0].text.strip().replace('"', '\\"').replace('\n', '\\n"\n"')
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


class XSDModelBuilder:
    def __init__(self, infile):
        self.models = {}
        self.fields = {}
        self.tree = etree.parse(infile)
        self.have_json = False

    def add_field(self, model_name, **kwargs):
        prefix = ''
        skip_code = False
        if 'code' not in kwargs:
            if kwargs.get('drop', False):
                template = '    # Dropping %(dotted_name)s field'
            elif kwargs.get('parent_field', False):
                template = '    # %(dotted_name)s field translates to this model\'s parent'
            elif 'one_to_many' in kwargs:
                template = ('    # %(name)s is declared as a reverse relation from %(options0)s\n'
                            '    # %(name)s = OneToManyField(%(one_to_many)s, %(serialized_options)s)')
            else:
                template = '    %(name)s = %(django_field)s(%(serialized_options)s)'
            if kwargs.get('coalesce'):
                kwargs['code'] = '    # %(dotted_name)s field coalesces to %(coalesce)s\n' % kwargs
                for f in self.models[model_name]['fields']:
                    if 'name' in f and f['name'] == kwargs['coalesce']:
                        skip_code = True
                        break
            else:
                if 'coalesce' in kwargs:
                    del kwargs['coalesce']
                kwargs['code'] = ''

            if kwargs.get('django_field') in ('models.ManyToManyField', 'models.ForeignKey'):
                for f in self.models[model_name]['fields']:
                    if f.get('django_field') == kwargs['django_field']:
                        if f['options'][0] == kwargs['options'][0]:
                            kwargs['options'].append('related_name="%s_as_%s"' % (camelcase_to_underscore(model_name), kwargs['name']))
                            break

            if not skip_code:
                kwargs['code'] += template % dict(kwargs,
                                                  options0=kwargs['options'][0] if kwargs.get('options') else '',
                                                  serialized_options=(', '.join(kwargs['options'])) if 'options' in kwargs else '')
        if 'django_field' in kwargs:
            kwargs['django_basefield'] = kwargs['django_field']
            for f in self.fields.values():
                if f['name'] == kwargs['django_field']:
                    kwargs['django_basefield'] = f['parent']
                    break
        self.models[model_name]['fields'].append(kwargs)

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
            options['max_length'] = length[0]
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
                options['max_length'] = match.group(2)
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
        doc = get_doc(st_def)
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
        name = '%sField' % typename
        code = 'class %(name)s(models.%(parent)s):\n' % {'name': name, 'parent': parent}

        if doc:
            code += '    description = "%s"\n\n' % doc

        if len(options):
            code += '    def __init__(self, *args, **kwargs):\n'
            for k, v in options.items():
                code += '        kwargs["%s"] = %s\n' % (k, v)
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

    def write_seq_or_choice(self, seq_or_choice, typename, prefix='', written=None, attrs=None, null=False):
        seq_def, choice_def = seq_or_choice
        if choice_def is not None:
            fields = self.models[get_model_for_type(typename)]['fields']
            n_start = len(fields)
            self.make_fields(typename, choice_def, prefix=prefix, written=written, attrs=attrs, null=True)
            fields[n_start]['code'] = '    # xs:choice start\n' + fields[n_start]['code']
            fields[-1]['code'] += '\n    # xs:choice end'
        elif seq_def is not None:
            self.make_fields(typename, seq_def, prefix=prefix, written=written, attrs=attrs, null=null)
        return ''

    def get_n_to_many_relation(self, typename, name, el_def):
        if el_def.get("maxOccurs") == 'unbounded':
            el2_def = el_def
            el2_name = name
        else:
            el2_def = xpath(self.get_element_complex_type(el_def), "xs:sequence/xs:element[@maxOccurs=$n]", n='unbounded')[0]
            el2_name = '%s_%s' % (name, el2_def.get("name"))
        ct2_def = self.get_element_complex_type(el2_def)
        if ct2_def is None:
            raise Exception("N_to_many field %s content is not a complexType\n" % name)
        rel = ct2_def.get("name") or ('%s.%s' % (typename, el2_name))
        return rel, ct2_def

    def get_one_to_one_relation(self, typename, name, el_type):
        try:
            ct2_def = xpath(self.tree, "//xs:complexType[@name=$n]", n=el_type)[0]
        except IndexError:
            raise Exception("one_to_one field %s content is not a complexType\n" % name)
        rel = ct2_def.get("name") or ('%s.%s' % (typename, name))
        return rel, ct2_def

    def make_fields(self, typename, seq_def, prefix='', written=None, attrs=None, null=False):
        def match(name, model, kind):
            fulltuple = model.get(kind, ()) + GLOBAL_MODEL_OPTIONS.get(kind, ())
            for expr in fulltuple:
                if re.match(expr + '$', name):
                    return True
            return False

        model_name = get_model_for_type(typename)
        model = MODEL_OPTIONS.get(model_name, {})
        if written is None:
            written = set()
        if attrs is None:
            attrs = []
        for choice_def in xpath(seq_def, "xs:choice"):
            self.write_seq_or_choice((None, choice_def), typename, prefix=prefix, written=written, attrs=attrs, null=null)
        for el_def in xpath(seq_def, "xs:element"):
            el_name = el_def.get("name")
            dotted_name = prefix + el_name
            name = dotted_name.replace('.', '_')
            el_type = self.get_element_type(el_def)

            if match(name, model, 'drop_fields'):
                self.add_field(model_name, dotted_name=dotted_name, drop=True)
                continue
            elif model.get('parent_field') == name:
                self.add_field(model_name, dotted_name=dotted_name, parent_field=True)
                continue

            coalesce_target = coalesce(name, model)
            if coalesce_target:
                name = coalesce_target

            if match(name, model, 'many_to_many_fields'):
                try:
                    rel = model.get('many_to_many_field_overrides', {})[name]
                    ct2_def = None
                except KeyError:
                    rel, ct2_def = self.get_n_to_many_relation(typename, name, el_def)
                self.make_model(rel, ct2_def)
                self.add_field(model_name, dotted_name=dotted_name, name=name, django_field='models.ManyToManyField', options=[get_model_for_type(rel), 'verbose_name="%s"' % get_doc(el_def)])
                written.add(name)
                continue

            elif match(name, model, 'one_to_many_fields'):
                reverse_name = camelcase_to_underscore(model_name)
                fk = {
                    'name': reverse_name,
                    'django_field': 'models.ForeignKey',
                    'options': ['"%s"' % model_name, 'on_delete=models.CASCADE', 'related_name="%s"' % name],
                }
                rel, ct2_def = self.get_n_to_many_relation(typename, name, el_def)
                self.make_model(rel, ct2_def, add_fields=[fk])
                self.add_field(model_name, dotted_name=dotted_name, name=name, one_to_many=True, options=[get_model_for_type(rel), 'verbose_name="%s"' % get_doc(el_def)], reverse_id_name=reverse_name + "_id")
                continue

            elif match(name, model, 'one_to_one_fields'):
                rel, ct2_def = self.get_one_to_one_relation(typename, name, el_type)
                self.make_model(rel, ct2_def)
                self.add_field(model_name, dotted_name=dotted_name, name=name, django_field='models.OneToOneField', options=[get_model_for_type(rel), 'on_delete=models.CASCADE', 'verbose_name="%s"' % get_doc(el_def), 'related_name="%s"' % camelcase_to_underscore(model_name), 'null=%s' % (null or get_null(el_def))])
                continue

            elif match(name, model, 'json_fields'):
                attrs.append((dotted_name, get_doc(el_def)))
                continue

            ct2_def = self.get_element_complex_type(el_def)
            flatten_prefix = name.startswith(GLOBAL_MODEL_OPTIONS.get('flatten_prefixes', ()) +
                                             model.get('flatten_prefixes', ()))
            flatten = match(name, model, 'flatten_fields')
            if (ct2_def is not None and flatten_prefix) or flatten:
                new_prefix = '%s.' % dotted_name
                if ct2_def is None:
                    raise Exception('complexType not found while flattening prefix %s' % new_prefix)
                null = null or get_null(el_def)
                ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
                if not ext2_defs:
                    seq_or_choice2_def = self.get_seq_or_choice(ct2_def)
                    seq_or_choice3_def = (None, None)
                else:
                    seq_or_choice2_def = self.get_seq_or_choice(ext2_defs[0])
                    basetype = ext2_defs[0].get("base")
                    ct3_def = xpath(self.tree, "//xs:complexType[@name=$n]", n=basetype)[0]
                    seq_or_choice3_def = self.get_seq_or_choice(ct3_def)
                fields = self.models[model_name]['fields']
                old_len = len(fields)
                self.write_seq_or_choice(seq_or_choice3_def, typename, prefix=new_prefix, attrs=attrs, written=written, null=null)
                self.write_seq_or_choice(seq_or_choice2_def, typename, prefix=new_prefix, attrs=attrs, written=written, null=null)
                if len(fields) == old_len:
                    raise Exception('    # SOMETHING STRANGE - flatten_fields RENDER VOID FOR %s\n' % new_prefix)
                continue

            if len(name) > 60:
                raise Exception("DJ_%s hits PostgreSQL 63 chars column name limit!" % name)

            basetype = None
            reference_extension = match(name, model, 'reference_extension_fields')
            if reference_extension:
                new_prefix = '%s.' % dotted_name
                if ct2_def is None:
                    raise Exception('complexType not found while processing reference extension for prefix %s' % new_prefix)
                ext2_defs = xpath(ct2_def, "xs:complexContent/xs:extension")
                basetype = ext2_defs[0].get("base")

            try:
                rel = model.get('foreign_key_overrides', {})[name]
                field = {'name': 'models.ForeignKey', 'options': [get_model_for_type(rel), 'on_delete=models.PROTECT']}
                self.make_model(rel)
            except KeyError:
                field = self.get_field(basetype or el_type, el_def, '%s.%s' % (typename, name))

            options = field.get('options', [])
            doc = get_doc(el_def)
            if doc:
                if field['name'] in ('models.ForeignKey', 'models.OneToOneField'):
                    options.append('verbose_name="%s"' % doc)
                else:
                    options[:0] = ['"%s"' % doc]

            null = null or get_null(el_def) or match(name, model, 'null_fields')
            if null:
                if field['name'] == 'models.BooleanField':
                    field['name'] = 'models.NullBooleanField'
                else:
                    options.append('null=True')
            max_occurs = el_def.get("maxOccurs", None)
            if max_occurs:
                raise Exception("caught maxOccurs=%s in %s.%s (@type=%s). Consider adding it to many_to_many_fields, one_to_many_fields or json_fields" % (max_occurs, typename, name, el_type))
            if name == model.get('primary_key', None):
                options.append('primary_key=True')
            elif match(name, model, 'unique_fields'):
                options.append('unique=True')
            elif match(name, model, 'index_fields'):
                options.append('db_index=True')
            self.add_field(model_name, dotted_name=dotted_name, name=name, django_field=field['name'], options=options, coalesce=coalesce_target)
            written.add(name)
            if reference_extension:
                seq_or_choice2_def = self.get_seq_or_choice(ext2_defs[0])
                self.write_seq_or_choice(seq_or_choice2_def, typename, prefix=new_prefix, attrs=attrs, written=written, null=null)
        if len(attrs) and not prefix:
            self.add_field(model_name, name='attrs', django_field='JSONField', options=['"JSON attributes: %s"' % '; '.join(['%s [%s]' % x for x in attrs]), 'null=True'])
            written.add('attrs')
            self.have_json = True

    def make_model(self, typename, ct_def=None, add_fields=None):
        typename = strip_ns(typename)

        if not get_model_for_type(typename):
            TYPE_MODEL_MAP[typename.replace('.', r'\.')] = typename
            sys.stderr.write('Automatic model name: %s. Consider adding it to TYPE_MODEL_MAP\n' % typename)

        model_name = get_model_for_type(typename)
        if model_name in self.models:
            return

        model = MODEL_OPTIONS.get(model_name, {})

        sys.stderr.write('Making model %s\n' % typename)

        self.models[model_name] = {'fields': []}

        parent = None
        meta = ''
        deps = []

        if not model.get('custom', False):
            if ct_def is None:
                ct_defs = xpath(self.tree, "//xs:complexType[@name=$n]", n=typename)
                if not ct_defs:
                    raise Exception("%s not found in schema" % typename)
                ct_def = ct_defs[0]

            doc = get_doc(ct_def)
            if doc:
                meta += '        verbose_name = "%s"\n' % doc

            fields = ''

            attr_defs = xpath(ct_def, "xs:attribute")
            if attr_defs is not None:
                for attr_def in attr_defs:
                    field = self.get_field(attr_def.get("type"))
                    options = field.get('options', [])
                    doc = get_doc(attr_def)
                    options[:0] = ['"%s"' % doc]
                    if attr_def.get("use") == "required":
                        options.append('null=True')
                    self.add_field(model_name, dotted_name="@%s" % attr_def.get("name"), name=attr_def.get("name"), django_field=field['name'], options=options)

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

            self.write_seq_or_choice((seq_def, choice_def), typename)

        if 'parent_type' in model:
            parent = model['parent_type']

        if not parent:
            parent = 'models.Model'
        else:
            parent = strip_ns(parent)
            self.make_model(parent)
            parent = get_model_for_type(parent)
            deps.append(parent)
            self.models[model_name]['parent'] = parent

        for f in model.get('add_fields', []) + (add_fields or []):
            self.add_field(model_name, **f)

        meta += ''.join(['        %s\n' % x for x in model.get('meta', ())])
        if meta:
            meta = '\n\n    class Meta:\n%s' % meta

        methods = '\n\n'.join(model.get('methods', ()))
        if methods:
            methods = '\n\n' + methods

        for f in self.models[model_name]['fields']:
            if f.get('django_field') in ('models.ForeignKey', 'models.OneToOneField', 'models.ManyToManyField'):
                if not f['options'][0].startswith('"'):
                    deps.append(f['options'][0])

        content = ('%(fields)s%(meta)s%(methods)s' % {
                     'fields': '\n'.join([f['code'] for f in self.models[model_name]['fields']]),
                     'meta': meta,
                     'methods': methods,
                 })
        if not content:
            content = '    pass'

        code = ('class %(name)s(%(parent)s):\n%(content)s\n\n' % {
                     'name': model_name,
                     'parent': parent,
                     'content': content,
                 })
        self.models[model_name]['code'] = code
        self.models[model_name]['deps'] = deps

        if 'match_fields' in model:
            self.models[model_name]['match_fields'] = model['match_fields']
        if 'preprocessor' in model:
            self.models[model_name]['preprocessor'] = model['preprocessor']

        sys.stderr.write('Done making model %s (%s)\n' % (model_name, typename))

    def make_models(self, typenames):
        for typename in typenames:
            self.make_model(typename)

    def write_model(self, model, outfile):
        if 'written' in model:
            return
        for dep in sorted(model['deps']):
            self.write_model(self.models[dep], outfile)
        outfile.write(model['code'].encode('utf-8'))
        model['written'] = True

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
            models_file.write('from .fields import %s\n\n\n' % ', '.join([x + 'Field' for x in sorted(self.fields.keys())]))
        for model in sorted(self.models.values()):
            self.write_model(model, models_file)
        json.dump(self.models, map_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    args = docopt(__doc__)

    builder = XSDModelBuilder(args['<xsd_filename>'])
    builder.make_models(args['<xsd_type>'])
    builder.write(open(args['<models_filename>'], "w"),
                  open(args['<fields_filename>'], "w"),
                  codecs.open(args['<mapping_filename>'], "w", 'utf-8'))
