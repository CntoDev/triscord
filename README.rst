Carpe Noctem Tactical Operations Trello to Discord integration script
=====================================================================

.. image:: https://travis-ci.org/CntoDev/triscord.svg?branch=master
    :target: https://travis-ci.org/CntoDev/triscord
    :alt: Build Status
.. image:: https://api.codacy.com/project/badge/Grade/bd599432409a4bac94dbe40c00c3a078
    :target: https://www.codacy.com/app/CNTODev/triscord?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CntoDev/triscord&amp;utm_campaign=Badge_Grade
    :alt: Codacy Grade
.. image:: https://api.codacy.com/project/badge/Coverage/bd599432409a4bac94dbe40c00c3a078
    :target: https://www.codacy.com/app/CNTODev/triscord?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CntoDev/triscord&amp;utm_campaign=Badge_Coverage
    :alt: Codacy Coverage
.. image:: https://requires.io/github/CntoDev/triscord/requirements.svg?branch=master
    :target: https://requires.io/github/CntoDev/triscord/requirements/?branch=master
    :alt: Requirements Status

Triscord is an utility script used by the Carpe Noctem Tacical Operations
community (http://carpenoctem.co) to provide a curated activity feed from
a given Trello board to a given Discord channel, using the Trello API in
one side, and a Discord Webhook in the other.

Requirements
------------

- Python 3.5
- Third-party libraries defined in the ``setup.py`` file.

Installation
------------

To install the script in your environment (using a ``virtualenv`` is
recommended), download the source code and run the following command from
the source's root directory.

.. code-block:: bash

    $ pip install .

Usage
-----

.. code-block:: bash

    $ triscord --help

    usage: triscord [-h] [--debug] --config-path CONFIG_PATH --persist-path
                    PERSIST_PATH

    Trello to Discord synchronisation script

    optional arguments:
      -h, --help            show this help message and exit
      --debug               Set debugging on
      --config-path CONFIG_PATH
                            Path of the configuration file
      --persist-path PERSIST_PATH
                            Path of the persistence file

Configuration
-------------

To properly configure the script you must create a configuration file following
a ini-like syntax. An example is available in the `triscord.ini.dist` file.

Please refer to Trello's API documentation as well as Discord's developper
documentation in order to generate the key/token pair as well as the webhook
url, respectively.
