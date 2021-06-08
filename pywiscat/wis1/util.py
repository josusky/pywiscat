# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2021 Government of Canada
# Copyright (c) 2021 IBL Software Engineering spol. s r. o.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import logging
import math
import os
from lxml import etree

LOGGER = logging.getLogger(__name__)

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'gts': 'http://www.isotc211.org/2005/gts',
    'xlink': 'http://www.w3.org/1999/xlink'
}


def search_files_by_term(directory: str, terms: list) -> list:
    """
    Searches directory tree of metadata for files containing search terms

    :param directory: directory to metadata files
    :param terms: list of terms

    :returns: list of file names
    """

    matches = []

    LOGGER.debug(f'Walking directory {directory}')
    match_count = 0
    file_count = 0
    for root, _, files in os.walk(directory):
        for name in files:
            filename = f'{root}/{name}'
            LOGGER.debug(filename)

            file_count += 1
            processed = math.floor(file_count * 100 / len(files))

            if not filename.endswith('.xml'):
                continue

            e = etree.parse(filename)
            anytext = ' '.join(
                [value.strip() for value in e.xpath('//text()')])

            if all(term.lower() in anytext.lower() for term in terms):
                match_count += 1
                LOGGER.debug(f'Found match #{match_count}, searched {processed}%')
                matches.append(filename)
            else:
                LOGGER.debug(f'No match found, searched {processed}%')

    LOGGER.debug(f'Found {len(matches)} matching metadata records.')
    return matches


def group_by_originator(file_list: list) -> dict:
    """
    Processes the given file list (MD records) and groups them by originator/pointOfContact

    :param file_list: list of MD XML files

    :returns: dict of results grouped by metadata originator
    """

    results_by_org = {}

    file_count = 0

    for file_path in file_list:

        parent_path, filename = os.path.split(file_path)
        LOGGER.debug(f'Analyzing: {filename}')

        e = etree.parse(file_path)

        file_count += 1
        analyzed = math.floor(file_count * 100 / len(file_list))

        try:
            element_xpath = '//gmd:CI_ResponsibleParty'
            code_list_value_xpath = "gmd:role/gmd:CI_RoleCode[@codeListValue='pointOfContact']"
            found = False
            for contact in e.xpath(element_xpath, namespaces=NAMESPACES):
                point_of_contact = contact.xpath(code_list_value_xpath, namespaces=NAMESPACES)
                if point_of_contact:
                    org_name = contact.xpath('gmd:organisationName/gco:CharacterString/text()', namespaces=NAMESPACES)  # noqa
                    LOGGER.debug(f'{contact.sourceline}: Found "{code_list_value_xpath}" with value "{org_name}"')
                    if org_name:
                        found = True
                        if org_name[0] in results_by_org:
                            LOGGER.debug(f'{contact.sourceline}: Adding to existing key, analyzed {analyzed}%')
                            results_by_org[org_name[0]] += 1
                        else:
                            LOGGER.debug(f'{contact.sourceline}: Adding to new key, analyzed {analyzed}%')
                            results_by_org[org_name[0]] = 1
                        break
            if not found:
                LOGGER.info(f'No {element_xpath} with {code_list_value_xpath} found in {filename}, analyzed {analyzed}%')

        except Exception as err:
            LOGGER.error(f'Error analyzing {filename}: {err}')

    return results_by_org
