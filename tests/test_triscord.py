# -*- coding: utf-8 -*-

"""triscord unit tests."""

import argparse
import logging
import os

import pytest
import requests

import triscord as unit
import triscord.persistence as persistence

from test_trello import api_actions

_ = api_actions


def test_main_function(mocker, api_actions, tmpdir_factory):  # pylint: disable=W0621
    """Asserts the main function if working properly."""

    mocker.patch('triscord.PARSER')
    mocker.patch('triscord.LOGGER')
    mocker.patch('requests.get')
    mocker.patch('requests.post')
    mocker.patch('triscord.discord.DiscordWebhook.send_message')

    persist_file_path = str(tmpdir_factory.mktemp('data').join('database.pickle3'))
    with persistence.persistent_storage(persist_file_path) as storage:
        storage['last_update'] = api_actions[-1]['date']

    unit.PARSER.parse_args = mocker.Mock(return_value=argparse.Namespace(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'fixtures',
            'triscord.ini'
        ),
        persist_path=persist_file_path,
        debug=True,
    ))

    unit.entry_point()
    unit.LOGGER.setLevel.assert_called_with(logging.DEBUG)  # pylint: disable=E1101
    unit.trello.TrelloAPI.get.assert_called_with(  # pylint: disable=E1101
        mocker.ANY,
        params=mocker.ANY,
    )
    unit.discord.DiscordWebhook.send_message.assert_called_with(  # pylint: disable=E1101
        mocker.ANY
    )


@pytest.mark.parametrize(
    "get_exception",
    [
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ]
)
def test_trello_unavailability(mocker, tmpdir_factory, get_exception):
    """Asserts the main function aborts if upstream trello API is unavailable."""

    mocker.patch('triscord.PARSER')
    mocker.patch('triscord.LOGGER')
    mocker.patch('triscord.trello.TrelloAPI.get', side_effect=get_exception)
    mocker.patch('triscord.discord.DiscordWebhook.send_message')

    persist_file_path = str(tmpdir_factory.mktemp('data').join('database.pickle3'))

    unit.PARSER.parse_args = mocker.Mock(return_value=argparse.Namespace(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'fixtures',
            'triscord.ini'
        ),
        persist_path=persist_file_path,
        debug=True,
    ))

    unit.entry_point()
    unit.LOGGER.setLevel.assert_called_with(logging.DEBUG)  # pylint: disable=E1101
    unit.trello.TrelloAPI.get.assert_called_with(  # pylint: disable=E1101
        mocker.ANY,
        params=mocker.ANY,
    )
    unit.discord.DiscordWebhook.send_message.assert_not_called()  # pylint: disable=E1101


#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
