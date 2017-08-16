This is a sample XSD from http://www.datypic.com/books/defxmlschema/chapter05.html.

The settings file demonstrates:
* XSD typename to Django model name mapping (`TYPE_MODEL_MAP`).
* `many_to_many_fields` usage.
* `primary_key` usage.
* `flatten_fields` usage for `xs:complexType/xs:simpleContent/xs:extension` fields.

An extra technique is demonstrated for different namespaces in multiple XSD files: a manually crafted "root" XSD file, `chapter05.xsd`, with `schemaLocation` references.

The resulting models look fairly well.

```
PYTHONPATH=. ../../../xsd_to_django_model/xsd_to_django_model.py chapter05.xsd OrderType
```
