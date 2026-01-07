# An OAI Static Repository and Data Provider for ArchivesSapce

There are two components to this service:

* A Python 3 script, [buildxml.py](util/buildxml.py), to build an [Open Archives Initiative](https://www.openarchives.org/pmh/) (OAI) [Static Repository](https://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm) from an ArchivesSpace repository using the ArchivesSpace API.  
* A Flask [web application](app/) that implements an OAI Data Provider to provide access to records in the Static Repository.


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

The Python 3 script, [ead2dc.py](app/ead2dc.py), takes as its input the Open Archives Initiative (OAI) output of an ArchivesSpace resource finding aid in Encoded Archival Description (EAD) format and outputs an XML file. The XML output contains Dublin Core (DC) records for digital resources found in the finding aid. Only records containing links to digital objects are included. The XML output is a 'static repository', inspired by the OAI Static Repository specification, but not adhering to it strictly. The static repository is the data source for the Open Archives Initiative (OAI) Data Provider.

The [OAI Data Provider](https://apps.library.caltech.edu/ead2dc/) adheres to the OAI standard and supports all the verbs (Identify, ListMetadataFormats, ListSets, ListIdentifiers, ListRecords, and GetRecord), resumption tokens, and sets. Only DC metadata is provided. Sets correspond to the archival collections in the Caltech Archives.

ead2dc - Main features and assumptions:

* Both input and output are OAI-compliant XML files.
* All 12 levels of EAD container are supported.
* Titles are inherited down the container hierarchy.
* All other metadata is mapped from the record containing the digital object references.
* Records without digital object references are ignored (i.e. not mapped to the output file)

OAI Data Provider - Main features and assumptions:

* The OAI Data Provider uses a static repository, i.e. it does not dynamically generate records.
* DC metadata only.
* Sets correspond to the archival collections and do not overlap.
* Records are delivered in batches of 250.

## Installation and Usage

The [ead2dc.py](app/ead2dc.py) file is designed to be run from the command line, or from within your favorite editing environment. It uses standard Python libraries and has been tested using Python 3.9.10 and 3.9.17.

The [OAI Data Provider](https://apps.library.caltech.edu/ead2dc/) is a web application written in Python 3 using the [Flask](https://flask.palletsprojects.com/en/3.0.x/) micro web framework. Installation of Flask will include dependent libraries, such as Jinja2 and werkzeug. No additional libraries are required.

## Mapping

| Element | Encoded Archival Description | Dublin Core |
|---|---|---|
| Collection title  | `archdesc/did/unittitle`  | `title`  |
| Container titles  | `dsc/c??/did/unittitle`  | `title`  |
| Personal creators  | `dsc/c??/did/origination label="creator"/persname`  | `creator`  |
| Corporate creators  | `dsc/c??/did/origination label="creator"/corpname`  | `creator`  |
| Dates  | `dsc/c??/did/unitdate`  | `date`  |
| Extent  | `dsc/c??/did/physdesc/extent`  | `extent`  |
| Description  | `dsc/c??/did/abstract`  | `description`  |
| Subject, general  | `dsc/c??/controlaccess/subject`  | `subject`  |
| Subject, geographic  | `dsc/c??/controlaccess/geogname`  | `subject`  |
| Subject, person  | `dsc/c??/controlaccess/persname`  | `subject`  |
| Subject, corporate  | `dsc/c??/controlaccess/corpname`  | `subject`  |
| Subject, activity  | `dsc/c??/controlaccess/function`  | `subject`  |
| Identifier  | `dsc/c??/did/unitid`  | `identifier`  |
| Identifier, link  | `dsc/c??/did/daogrp/daoloc['xlink:href']`  | `identifier`  |


## Example

Paul B. MacCready Papers ca. 1931-2002, Caltech Archives

* [Finding Aid](https://collections.archives.caltech.edu/repositories/2/resources/197)
* [ArchivesSpace OAI Data Provider output](https://caltechlibrary.github.io/ead2dc/xml/maccready-ead.xml)
* [OAI Static Repository created by ead2dc](https://caltechlibrary.github.io/ead2dc/xml/maccready-dc.xml)


## License

Software produced by the Caltech Library is Copyright © 2023 California Institute of Technology.  This software is freely distributed under a BSD-style license.  Please see the [LICENSE](LICENSE) file for more information.


## References

* [OAI Static Repositories](http://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm)
* [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
* [Dublin Core Qualifiers](https://www.dublincore.org/specifications/dublin-core/dcmes-qualifiers/)
* [Guidelines for implementing DC in XML](https://www.dublincore.org/specifications/dublin-core/dc-xml-guidelines/2002-04-14/)


## Acknowledgments

This work was funded by the California Institute of Technology Library.