# xsd_to_django_model
Generate Django models from an XSD schema description (and a bunch of hints)

## TODO
* More documentation.
* Examples.

## Getting started

```
Usage:
    xsd_to_django_model.py [-m <models_filename>] [-f <fields_filename>] [-j <mapping_filename>] <xsd_filename> <xsd_type>...
    xsd_to_django_model.py -h | --help

Options:
    -h --help              Show this screen.
    -m <models_filename>   Output models filename [default: models.py].
    -f <fields_filename>   Output fields filename [default: fields.py].
    -j <mapping_filename>  Output JSON mapping filename [default: mapping.json].
    <xsd_filename>         Input XSD schema filename.
    <xsd_type>             XSD type (or an XPath query for XSD type) for which a Django model should be generated.

If you have xsd_to_django_model_settings.py in your PYTHONPATH or in the current directory, it will be imported.
```
