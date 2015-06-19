=============
ckanext-ceon
=============

Extension implementing various CeON changes to default CKAN installation.
The part handling DOI is based upon https://github.com/NaturalHistoryMuseum/ckanext-doi


------------
Requirements
------------

The extension is being tested with latest development version (2.4a at the
moment).  However it should probably work fine with ckan-2.3 as well.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-ceon:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-ceon Python package into your virtual environment::

     pip install ckanext-ceon

3. Add ``ceon`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

Document any optional config settings here. For example::

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.ceon.some_setting = some_default_value


------------------------
Development Installation
------------------------

To install ckanext-ceon for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/mateuszneumann/ckanext-ceon.git
    cd ckanext-ceon
    python setup.py develop
    export C_INCLUDE_PATH="/usr/include/libxml2:/usr/include/libxslt"
    pip install -r dev-requirements.txt

