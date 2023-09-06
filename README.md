# ArchiveSpace OAI/EAD to OAI/DC Conversion

A Python 3 script to convert ArchivesSpace Encoded Archival Description (EAD) finding aids to Dublin Core (DC) records.

[![License](https://img.shields.io/badge/License-BSD--like-lightgrey)](https://choosealicense.com/licenses/bsd-3-clause)


## Table of contents

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
* [Mapping](#mapping)
* [Example](#example)
* [License](#license)
* [References](#references)
* [Acknowledgments](#acknowledgments)


## Introduction

This tool takes as its input the Open Archives Initiative (OAI) output of an ArchivesSpace resource finding aid in Encoded Archival Description (EAD) format and converts it to an OAI Static Repository containing DC metadata records with links to digital objects. 

Main features and assumptions:

* Both input and output are OAI-compliant XML files.
* All 12 levels of EAD container are supported.
* Titles are inherited down the container hierarchy.
* All other metadata is mapped from the record containing the digital object references.
* Records without digital object references are ignored (i.e. not mapped to the output file)
* Records with non-image object references are ignored (e.g. video)


## Installation

No installation is required. The [ead2dc.py](ead2dc.py) file is designed to be run from the command line, or from within your favorite editing environment.
 

## Usage

At the moment this is a command line script designed to be directly edited before each execution. See the [ead2dc.py](ead2dc.py) file for information. It uses standard Python libraries and has been tested using Python 3.9.17


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
* [ArchivesSpace OAI Data Provider output](https://caltechlibrary.github.io/ead2dc/maccready-ead.xml)
* [OAI Static Repository created by ead2dc](https://caltechlibrary.github.io/ead2dc/maccready-dc.xml)


## License

Software produced by the Caltech Library is Copyright © 2023 California Institute of Technology.  This software is freely distributed under a BSD-style license.  Please see the [LICENSE](LICENSE) file for more information.


## References

* [OAI Static Repositories](http://www.openarchives.org/OAI/2.0/guidelines-static-repository.htm)
* [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
* [Dublin Core Qualifiers](https://www.dublincore.org/specifications/dublin-core/dcmes-qualifiers/)
* [Guidelines for implementing DC in XML](https://www.dublincore.org/specifications/dublin-core/dc-xml-guidelines/2002-04-14/)


## Acknowledgments

This work was funded by the California Institute of Technology Library.