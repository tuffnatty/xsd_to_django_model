This is an XSD for Russian Land Survey Plan from https://rosreestr.ru/site/fiz/zaregistrirovat-nedvizhimoe-imushchestvo-/xml-skhemy/

The settings are tweaked just enough to generate some models file without crashing. Additional work has to be done with deep examination of real data.

```
PYTHONPATH=. ../../../xsd_to_django_model/xsd_to_django_model.py MP_v06.xsd //xs:element[@name="MP"]/xs:complexType
```
