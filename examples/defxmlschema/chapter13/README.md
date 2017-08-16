This is a sample XSD from http://www.datypic.com/books/defxmlschema/chapter13.html.

It contains XSD features which we can't process yet.

The settings file demonstrates:
* XSD typename to Django model name mapping (`TYPE_MODEL_MAP`).
* `flatten_fields` usage for `xs:complexType/xs:simpleContent` fields (FIXME: the field is missing in model due to unsupported `xs:complexType/xs:simpleContent/xs:restriction`.
* `flatten_fields` usage for `xs:complexType/xs:complexContent` fields.
* `TYPE_OVERRIDES` usage for overriding a primitive field type which we don't yet support.

```
PYTHONPATH=. ../../../xsd_to_django_model/xsd_to_django_model.py chapter13.xsd ItemsType
```
