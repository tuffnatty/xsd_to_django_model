This is a sample XSD from http://www.datypic.com/books/defxmlschema/chapter12.html.

It contains some XSD features which we can't process automatically, but with tweaked settings, the resulting model looks fairly well.

The settings file demonstrates:
* XSD typename to Django model name mapping (`TYPE_MODEL_MAP`).
* `flatten_fields` usage for `xs:complexType/xs:simpleContent/xs:extension` fields.
* `flatten_fields` usage for `xs:complexType/xs:complexContent` fields.
* `coalesce_fields` usage for renaming a field produced by flattening an `xs:complexType` with just a single attribute.
* `TYPE_OVERRIDES` usage for overriding a field type which cannot be introspected automatically.

```
PYTHONPATH=. ../../../xsd_to_django_model/xsd_to_django_model.py chapter12.xsd ItemsType
```
