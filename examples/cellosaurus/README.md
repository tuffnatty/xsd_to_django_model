This is an XSD from https://ftp.expasy.org/databases/cellosaurus/cellosaurus.xsd

The original XSD had a typo which I have fixed:

```
--- cellosaurus.xsd.orig        2023-07-27 22:31:27.330888000 +0300
+++ cellosaurus.xsd     2023-07-27 22:31:54.856313000 +0300
@@ -65,7 +65,7 @@
        </xs:annotation>
        <xs:complexType>
           <xs:sequence>
-             <xs:element name="terminology" minOccurs="1" maxOccurs="unbounded"/>
+             <xs:element ref="terminology" minOccurs="1" maxOccurs="unbounded"/>
           </xs:sequence>
        </xs:complexType>
    </xs:element>
```

The XSD is very XML-ish and not very RDBMS-ish. Nevertheless, something can be done:

```
PYTHONPATH=. ../../xsd_to_django_model/xsd_to_django_model.py cellosaurus.xsd /Cellosaurus
pip install django
django-admin.py startproject cellosaurus-project
cd cellosaurus-project
./manage.py startapp cellosaurus
cp ../models.py cellosaurus/models.py
./manage.py makemigrations cellosaurus  # Ok!
```

