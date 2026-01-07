# An OAI Static Repository and Data Provider for ArchivesSpace

There are two components to this service:

* A Python 3 script, [buildxml.py](util/buildxml.py), to build an [Open Archives Initiative](https://www.openarchives.org/pmh/) (OAI) [Static Repository](https://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm) from an ArchivesSpace (AS) repository using the AS API.  
* A Flask [web application](app/) that implements an OAI Data Provider to provide access to records in the Static Repository.
* The name of this repository, [ead2dc](https://github.com/caltechlibrary/ead2dc), is a misnomer, referring to a former version that transformed AS EAD output to generate the static repository.


[![License](https://img.shields.io/badge/License-BSD--like-lightgrey)](https://choosealicense.com/licenses/bsd-3-clause)


## Table of contents

* [Introduction](#introduction)
* [Installation and Usage](#installation-and-usage)
* [Mapping](#mapping)
* [Example](#example)
* [License](#license)
* [References](#references)
* [Acknowledgments](#acknowledgments)


## Introduction

The Python 3 script, [buildxml.py](util/buildxml.py), connects with a specific ArchivesSpace repository via the AS API, scans the digital objects in the repository, finds the associated archival objects, and writes the OAI Static Repository XML file. The XML output contains Dublin Core (DC) records for digital resources. The XML static repository is based on the [OAI Static Repository specification](https://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm), but does not adhering to it strictly. The static repository is the data source for the Open Archives Initiative (OAI) Data Provider.

The [OAI Data Provider](https://apps.library.caltech.edu/ead2dc/) adheres to the OAI standard and supports all the verbs (Identify, ListMetadataFormats, ListSets, ListIdentifiers, ListRecords, and GetRecord), resumption tokens, and sets. Only DC metadata is provided. Sets correspond to the archival collections in the Caltech Archives.

Main features and assumptions:

* The output of the Data Provider is OAI-compliant, as tested using this [OAI-PMH Validator](https://validator.oaipmh.com/).
* Each DC record includes a single title. Other titles in a finding aid hierarchy (collection, series, subseries, etc.) are included in DC:relation.
* Descriptive metadata is drawn from archival object records.
* Only digital objects are included. Archives object records without digital content are omitted.
* The OAI Data Provider uses a static repository, i.e. it does not dynamically generate records.
* DC metadata only.
* Sets correspond to the archival collections and do not overlap.
* Records are delivered in batches of 250.

## Installation and Usage

### buildxml

The [buildxml.py](util/buildxml.py) file is designed to be run from the command line, or from within your favorite editing environment. It uses standard Python libraries and has been tested using Python 3.9 through 3.12.

### Data Provider

The [OAI Data Provider](https://apps.library.caltech.edu/ead2dc/) is a web application written in Python 3 using the [Flask](https://flask.palletsprojects.com/en/3.0.x/) micro web framework. Installation of Flask will include dependent libraries, such as Jinja2 and werkzeug. No additional libraries are required.

### Defaults

### Common services





## Example



## License

Software produced by the Caltech Library is Copyright © 2026 California Institute of Technology.  This software is freely distributed under a BSD-style license.  Please see the [LICENSE](LICENSE) file for more information.


## References

* [OAI Static Repositories](http://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm)
* [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
* [Dublin Core Qualifiers](https://www.dublincore.org/specifications/dublin-core/dcmes-qualifiers/)
* [Guidelines for implementing DC in XML](https://www.dublincore.org/specifications/dublin-core/dc-xml-guidelines/2002-04-14/)


## Acknowledgments

This work was funded by the California Institute of Technology Library.