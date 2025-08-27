.. TCSPC Confocal Microscopy at Purdue documentation master file, created by
   sphinx-quickstart on Tue Jul 22 16:23:47 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. Order of Operations to add docstrings to main sphinx docs. Please follow these steps in order!
   It will make things a lot easier for us to keep track of.

   Step 1: Add descriptive and useful docstrings to the functions. They can be
   added within triple quotations like this:
   """ This is a simple template GUI measurement module for qudi.
   """
   This allows Sphinx to auto-detect documentation.

   Step 2: Create a .rst file for your document in the relevant directory. I've created
   4 separate folders, one each for GUIs, logic, interfaces, and hardware. An example .rst file
   is provided in the source directory for your reference. All you need to do is make a copy of that file
   into the right directory. By default, hidden methods (those that start with an underscore _ ) do not show up
   in the documentation. If there are certain functions you'd like mentioned, you can add the field 'private_members:'
   to the .rst files and manually list out the function names. This is done so that only those methods are mentioned.
   
   
   
   
   Please put the right
   .rst file in the right directory. PLEASE DO NOT MOVE ANY FILES WITHOUT CONFIRMATION. THIS WILL INTERFERE
   WITH THE RENDERING OF THE DOCUMENTATION.
   

Welcome to TCSPC Confocal Microscopy at Purdue's documentation!
===============================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   qudi_core
   gui_docs/template
   gui_docs/counter
   gui_docs/daq_counter
   gui_docs/flippermirror
   gui_docs/galvo
   gui_docs/lacpid
   gui_docs/lifetime
   gui_docs/ltunelaser
   gui_docs/manualLAC
   gui_docs/polarization_measurement
   gui_docs/polarization_motor
   gui_docs/powermeter
   gui_docs/qutag
   gui_docs/saturation
   gui_docs/scanner



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
