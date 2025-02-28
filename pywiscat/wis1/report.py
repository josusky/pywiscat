# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ján Osuský <jan.osusky@iblsoft.com>
#
# Copyright (c) 2021 Tom Kralidis
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

import json
import logging

import click

from pywiscat.cli_helpers import cli_callbacks
from pywiscat.wis1.util import (create_file_list, search_files_by_term, group_by_originator)

LOGGER = logging.getLogger(__name__)


@click.group()
def report():
    """Reporting functions"""
    pass


def group_search_results_by_organization(directory: str, terms: list) -> dict:
    """
    Searches directory tree of metadata for matching search terms and
    and groups by organization

    :param directory: directory to metadata files
    :param terms: list of terms

    :returns: dict of results grouped by organization
    """

    matches = search_files_by_term(directory, terms)
    matches_by_org = group_by_originator(matches)
    return matches_by_org


@click.command()
@click.pass_context
@cli_callbacks
@click.option('--directory', '-d', required=False,
              help='Directory with metadata files to process',
              type=click.Path(resolve_path=True, file_okay=False))
@click.option('--term', '-t', 'terms', multiple=True, required=True)
@click.option('--file-list', '-f', 'file_list_file',
              type=click.Path(exists=True, resolve_path=True), required=False,
              help='File containing JSON list with metadata files to process, alternative to "-d"')
def terms_by_org(ctx, terms, directory, file_list_file, verbosity):
    """Analyze term searches by organization"""

    if file_list_file is None and directory is None:
        raise click.UsageError('Missing --file-list or --directory option')

    results = {}
    if not file_list_file:
        click.echo(f'Analyzing records in {directory} for terms {terms}')
        results = group_search_results_by_organization(directory, terms)
    else:
        file_list = []
        with open(file_list_file, "r", encoding="utf-8") as file_list_json:
            try:
                file_list = json.load(file_list_json)
            except Exception as err:
                LOGGER.error(f'Failed to read file list {file_list_file}: {err}')
                return
            results = group_by_originator(file_list)

    if results:
        click.echo(json.dumps(results, indent=4))
    else:
        click.echo('No results')


@click.command()
@click.pass_context
@cli_callbacks
@click.option('--directory', '-d', required=False,
              help='Directory with metadata files to process',
              type=click.Path(resolve_path=True, file_okay=False))
@click.option('--file-list', '-f', 'file_list_file',
              type=click.Path(exists=True, resolve_path=True), required=False,
              help='File containing JSON list with metadata files to process, alternative to "-d"')
def records_by_org(ctx, directory, file_list_file, verbosity):
    """Report number of records by organization / originator"""

    if file_list_file is None and directory is None:
        raise click.UsageError('Missing --file-list or --directory option')

    results = {}
    if not file_list_file:
        click.echo(f'Analyzing records in {directory}')
        file_list = create_file_list(directory)
        results = group_by_originator(file_list)
    else:
        file_list = []
        with open(file_list_file, "r", encoding="utf-8") as file_list_json:
            try:
                file_list = json.load(file_list_json)
            except Exception as err:
                LOGGER.error(f'Failed to read file list {file_list_file}: {err}')
                return
            results = group_by_originator(file_list)

    if results:
        click.echo(json.dumps(results, indent=4))
    else:
        click.echo('No results')


report.add_command(terms_by_org)
report.add_command(records_by_org)
