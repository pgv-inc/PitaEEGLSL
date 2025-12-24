.. pitaeeg documentation master file

Welcome to pitaeeg's documentation!
====================================

**pitaeeg** is a Python package that provides an easy-to-use interface for communicating with PitaEEG sensor devices.

.. note::
   This package requires a proprietary native library. Please contact support@pgv.co.jp for library licensing information.

Quick Start
-----------

Install the package:

.. code-block:: bash

   pip install pitaeeg

Basic usage:

.. code-block:: python

   from pitaeeg import Sensor

   with Sensor(port="COM3") as sensor:
       sensor.connect("HARU2-001", scan_timeout=10.0)
       devicetime_ms = sensor.start_measurement()
       
       for data in sensor.receive_data():
           print(f"Channels: {data.data}, Battery: {data.batlevel}%")
           break

For more examples, see the `examples <https://github.com/pgv-inc/PitaEEGLSL/tree/main/examples>`_ directory.

Contents
--------

.. toctree::
   :maxdepth: 4
   :caption: API Reference:

   pitaeeg

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
