# -*- coding: utf-8 -*-

"""triscord.trello unit tests."""

import json
import os
import re
import unittest.mock

import pytest
import requests

from triscord import trello as unit


def _load_from_json(file_name):
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures', file_name)
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


@pytest.fixture(scope="module")
def api_config():
    """Returns basic Trello API configuration."""

    return {
        'url': "https://dummy.tld/1",
        'key': "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        'token': "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        'board_id': "AAAAAAAA",
    }


def test_api_authentication(mocker, api_config):  # pylint: disable=W0621
    """Asserts that TrelloApi properly format requests credentials to Trello's API."""

    mocker.patch('requests.get')

    endpoint = '/boards/{board_id}'.format(board_id=api_config['board_id'])

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    api.get(endpoint)

    requests.get.assert_called_with(  # pylint:disable=E1101
        api_config['url'] + endpoint,
        params={
            'key': api_config['key'],
            'token': api_config['token'],
        },
    )


@pytest.fixture(scope="function")
def api_actions(mocker):
    """Fixture generating and mocking Trello's API endpoint for board actions."""

    actions = _load_from_json('trello_api_actions.json')

    original_get = unit.TrelloAPI.get

    def side_effect(endpoint, *args, params={}, **kwargs):
        """Endpoint router side effect."""

        match = re.match(r'\/boards\/([^\/]+)\/actions', endpoint)
        if match:
            filtered_action_types = params['filter'].split(',')
            activity = []
            for action in actions:
                if action['type'] not in filtered_action_types:
                    pytest.mark.skip(
                        reason="Unsupported/muted action type `{}`".format(action['type'])
                    )
                else:
                    activity.append(action)

            inner = unittest.mock.Mock()
            inner.json = unittest.mock.Mock(return_value=activity)
            return inner
        else:  # pragma: no cover
            return original_get(endpoint, *args, **kwargs)

    mocker.patch('triscord.trello.TrelloAPI.get', side_effect=side_effect)

    return actions


def test_actions_fetching(api_config, api_actions):  # pylint: disable=W0621
    """Asserts that TrelloActivityFeed properly manages fetching a given board's actions."""

    _ = api_actions

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )

    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    assert any(feed.actions)


def test_action_type_filter(mocker, api_config):  # pylint: disable=W0621
    """Asserts that TrelloActivityFeed properly constructs `filter` param for action listing."""

    mocked_response = unittest.mock.Mock()
    mocked_response.json = unittest.mock.Mock(return_value=[])
    side_effect = unittest.mock.Mock(return_value=mocked_response)
    mocker.patch('triscord.trello.TrelloAPI.get', side_effect=side_effect)

    endpoint = '/boards/{board_id}/actions'.format(board_id=api_config['board_id'])
    muted_action_types = ['addMemberToCard', ]

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    _ = list(feed.actions)
    unit.TrelloAPI.get.assert_called_once_with(  # pylint:disable=E1101
        endpoint,
        params=mocker.ANY,
    )
    _, kwargs = unit.TrelloAPI.get.call_args  # pylint:disable=E1101
    assert not any(set(muted_action_types) - set(kwargs['params']['filter'].split(',')))


def test_action_update_filter(api_config, api_actions):  # pylint: disable=W0621
    """Asserts that TrelloActivityFeed properly filters out unwanted updateCard instances."""

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )

    muted_update_fields = ["idList"]
    if not any(filter(
            lambda action: action['type'] == "updateCard" and
            any(set(muted_update_fields) - set(action['data']['old'].keys())),
            api_actions
    )):  # pragma: no cover
        pytest.mark.skip(reason="No updateCard action present in fixture")

    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
        muted_update_fields=muted_update_fields,
    )
    for action in feed.actions:
        if action['type'] == "updateCard":
            for muted_field in muted_update_fields:
                assert muted_field not in action['data']['old']


@pytest.fixture(scope="function", params=_load_from_json('trello_api_actions.json'))
def api_action(mocker, request):
    """Fixture providing a single Board activity action."""

    action = request.param

    original_get = unit.TrelloAPI.get

    def side_effect(endpoint, *args, params, **kwargs):
        """Endpoint router side effect."""

        match = re.match(r'\/boards\/([^\/]+)\/actions', endpoint)
        if match:
            filtered_action_types = params['filter'].split(',')
            activity = []
            if action['type'] not in filtered_action_types:
                pytest.mark.skip(
                    reason="Unsupported/muted action type `{}`".format(action['type'])
                )
            else:
                activity.append(action)

            inner = unittest.mock.Mock()
            inner.json = unittest.mock.Mock(return_value=activity)
            return inner
        else:  # pragma: no cover
            return original_get(endpoint, *args, params, **kwargs)

    mocker.patch('triscord.trello.TrelloAPI.get', side_effect=side_effect)

    return action


def test_action_formatting(api_config, api_action):  # pylint: disable=W0621
    """Asserts proper formatting of action messages."""

    _ = api_action
    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    for action in feed.actions:
        print("got action: ", action['type'])
        message = feed.format_action(action)
        assert any(message)


#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
