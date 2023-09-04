# ArchiveSpace OAI/EAD to OAI/DC Conversion

A Python 3 script to convert ArchivesSpace Encoded Archival Description (EAD) finding aids to Dublin Core (DC) records.

[![License](https://img.shields.io/badge/License-BSD--like-lightgrey)](https://choosealicense.com/licenses/bsd-3-clause)


## Table of contents

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
* [Example](#example)
* [License](#license)
* [References](#references)
* [Acknowledgments](#acknowledgments)


## Introduction

This tool takes as its input the Open Archives Initiative (OAI) output of an ArchivesSpace resource finding aid in Encoded Archival Description (EAD) format and converts it to an OAI Static Repository containing DC metadata records with links to digital objects. 

The main features of the tool are:

* Both input and output are OAI-compliant XML files.
* All 12 levels of EAD container are supported.
* Titles are inherited down the container hierarchy.
* All other metadata is mapped from the record containing the digital object references.
* Records without digital object references are ignored (i.e. not mapped to the output file)


## Installation

No installation is required. The [ead2dc.py](ead2dc.py) file is designed to be run from the command line, or from within your favorite editing environment.
 

## Usage

At the moment this is a command line script designed to be directly edited before each execution. See the [ead2dc.py](ead2dc.py) file for information. It uses standard Python libraries and has been tested using Python 3.9.17


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