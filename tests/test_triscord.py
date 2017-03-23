# -*- coding: utf-8 -*-

"""triscord unit tests."""

import argparse
import logging
import os

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


#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
