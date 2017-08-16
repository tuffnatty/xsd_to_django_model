This is a sample XSD from http://www.datypic.com/books/defxmlschema/chapter04.html.

The resulting models look fairly well. Additional XSD files are automatically imported using `xs:import[@schemaLocation]` and `xs:include[@schemaLocation]`.

The settings file demonstrates:
* XSD typename to Django model name mapping (`TYPE_MODEL_MAP`).
* `flatten_fields` usage for `xs:complexType/xs:simpleContent/xs:extension` fields.
* `flatten_fields` usage for `xs:complexType/xs:complexContent` fields.

```
PYTHONPATH=. ../../../xsd_to_django_model/xsd_to_django_model.py chapter04ord1.xsd OrderType
```
