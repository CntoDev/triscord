# -*- coding: utf-8 -*-

"""triscord.trello unit tests."""
import copy
import json
import os
import re
import unittest.mock

import arrow
import pytest
import requests

from triscord import trello as unit
from triscord import settings


def _load_from_json(file_name):
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures', file_name)
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def _filter_action_type(actions, type_whitelist):
    for action in actions:
        if action['type'] in type_whitelist:
            yield action


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
        return original_get(endpoint, *args, **kwargs)  # pragma: no cover

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


def test_action_update_listfilter(api_config, api_actions):  # pylint: disable=W0621
    """Asserts that TrelloActivityFeed properly filters out updateCard instances from blacklisted
    lists."""

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )

    muted_lists = ["Blacklisted List"]
    assert list(filter(
        lambda action: action['type'] == "updateCard" and
        'listAfter' in action['data'] and
        action['data']['listAfter']['name'] in muted_lists,
        api_actions
    ))

    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
        muted_update_lists=muted_lists,
    )
    for action in feed.actions:
        if action['type'] == "updateCard":
            if 'listAfter' in action['data']:
                assert action['data']['listAfter']['name'] not in muted_lists


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
        message = feed.format_action(action)
        if action['type'] == 'updateCard':
            # Assert updateCard supressions
            if 'idLabels' in action['data']['old'] or \
               'membersList' in action['data']['old']:
                assert message is None
                continue
        assert any(message)


@pytest.mark.parametrize(
    'action',
    _filter_action_type(
        _load_from_json('trello_api_action_card_assigned.json'),
        ['addMemberToCard'],
    ),
)
def test_action_cardjoin(api_config, action):  # pylint: disable=W0621
    """Regression test.

    Asserts that `addMemberToCard` action formatting outputs the actual added member.
    The bug was that we were using the action instigator rather than the assigned member.
    """

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    assigned_member = action['member']['username']
    message = feed.format_action(action)
    assert assigned_member in message


@pytest.mark.parametrize(
    'action',
    _filter_action_type(
        _load_from_json('trello_api_action_card_assigned.json'),
        ['updateCard'],
    ),
)
def test_action_cardjoin_duplicate(api_config, action):  # pylint: disable=W0621
    """Regression test.

    Asserts that updateCard actions that only update assigned members are ignored.
    Trello updated their API to add such an action *in addition* to the addMemberToCard.
    """

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    message = feed.format_action(action)
    assert message is None


@pytest.mark.parametrize(
    'action',
    _filter_action_type(
        _load_from_json('trello_api_action_card_assigned.json'),
        ['removeMemberFromCard'],
    ),
)
def test_action_cardleave(api_config, action):  # pylint: disable=W0621
    """Regression test.

    Asserts that `removeMemberToCard` action formatting outputs the actual removed member.
    The bug was that we were using the action instigator rather than the unassigned member.
    """

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )
    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )
    assigned_member = action['member']['username']
    message = feed.format_action(action)
    assert assigned_member in message


def test_actions_ordering(api_config, api_actions):  # pylint: disable=W0621
    """Regression test.

    Asserts that TrelloActivityFeed ouputs actions in a chronological order.
    The bug was that actions were displayed using Trello's API original order,
    which is reversed chronologically.
    """

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

    previous_action_date = None
    for action in feed.actions:
        action_date = arrow.get(action['date'])
        if previous_action_date is not None:
            assert action_date > previous_action_date
        previous_action_date = action_date


def test_username_aliases(api_config, api_actions):  # pylint: disable=W0621
    """Asserts Trello usernames are changed with configured aliases"""

    unmodified_actions = copy.deepcopy(api_actions)

    api = unit.TrelloAPI(
        key=api_config['key'],
        token=api_config['token'],
        base_url=api_config['url'],
    )

    feed = unit.TrelloActivityFeed(
        api=api,
        board_id=api_config['board_id'],
    )

    unmuted_actions = [action for action in unmodified_actions if action['type'] in
                       unit.TrelloActivityFeed.action_formatters.keys()]
    unmuted_actions.reverse()

    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures',
                               'triscord.ini')

    settings.CONFIG.read(config_path)
    aliases = settings.CONFIG['Aliases']

    for index, action in enumerate(feed.actions):
        trello_username = unmuted_actions[index]['memberCreator']['username']
        if trello_username in aliases:
            assert action['memberCreator']['username'] == aliases[trello_username]
            assert action['display']['entities']['memberCreator']['username'] == \
                aliases[trello_username]
            if 'member' in action:
                assert action['member']['username'] == aliases[trello_username]


#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
