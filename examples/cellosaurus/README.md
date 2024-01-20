This is an XSD from https://ftp.expasy.org/databases/cellosaurus/cellosaurus.xsd

The XSD is very XML-ish and not very RDBMS-ish. Nevertheless, something can be done:

```bash
PYTHONPATH=. ../../xsd_to_django_model/xsd_to_django_model.py cellosaurus.xsd /Cellosaurus
pip install django
django-admin.py startproject cellosaurus-project
cd cellosaurus-project
./manage.py startapp cellosaurus
cp ../models.py cellosaurus/models.py
./manage.py makemigrations cellosaurus  # Ok!
```

# Cellosaurus Version 6.10's XSD Bug

Cellosaurus version 6.10's XSD had a typo in `name` vs `ref`, which can be fixed:

```
--- cellosaurus.xsd.orig        2023-07-27 22:31:27.330888000 +0300
+++ cellosaurus.xsd     2023-07-27 22:31:54.856313000 +0300
@@ -65,7 +65,7 @@
        </xs:annotation>
        <xs:compleqxType>
           <xs:sequence>
-             <xs:element name="terminology" minOccurs="1" maxOccurs="unbounded"/>
+             <xs:element ref="terminology" minOccurs="1" maxOccurs="unbounded"/>
           </xs:sequence>
        </xs:complexType>
    </xs:element>
```

Note that Cellosaurus corrected this mistake in version 7.00,
released on October 5th, 2023.
