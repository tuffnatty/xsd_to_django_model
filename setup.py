from setuptools import setup

import xsd_to_django_model


setup(
    name='xsd_to_django_model',
    version=xsd_to_django_model.__version__,
    url='http://github.com/tuffnatty/xsd_to_django_model',
    license='GNU General Public License v3 (GPLv3)',
    author='Phil Krylov',
    author_email='phil.krylov@gmail.com',
    description='Generate Django models from an XSD schema description (and a bunch of hints)',
    packages=['xsd_to_django_model'],
    platforms='any',
    install_requires=['docopt', 'xmlschema'],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Database',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: XML',
    ],
    scripts=['xsd_to_django_model/xsd_to_django_model.py']
)
