# -*- coding: utf-8 -*-

"""Trello interactions module."""

import logging

import arrow
import requests


class TrelloAPI(object):  # pylint: disable=R0903
    """Provides an abstraction to Trello's Web authentication-restricted API."""

    def __init__(self, key, token, base_url="https://api.trello.com/1"):
        self.key = key
        self.token = token
        self.base_url = base_url

    @property
    def _base_payload(self):
        """Contains the authentication credentials required for a request."""
        return {
            'key': self.key,
            'token': self.token,
        }

    def _method(self, name, endpoint, *args, **kwargs):
        """Injects authentication, executes the request and verify response status code."""

        payload_key_name = 'params' if name == 'get' else 'data'
        if payload_key_name not in kwargs:
            kwargs[payload_key_name] = dict()
        kwargs[payload_key_name].update(self._base_payload)

        url = self.base_url + endpoint
        response = requests.__dict__[name](url, *args, **kwargs)
        response.raise_for_status()
        logging.debug("TrelloAPI.%s(%s): %s", name, endpoint, response)
        return response

    def get(self, endpoint, *args, **kwargs):
        """Provides access to the HTTP GET method on the API."""

        return self._method('get', endpoint, *args, **kwargs)


class TrelloActivityFeed(object):
    """Provides an interface for fetching all actions that happened in a Trello board."""

    action_formatters = dict()

    def __init__(self,  # pylint: disable=R0913
                 api,
                 board_id,
                 muted_action_types=None,
                 muted_update_fields=None,
                 muted_update_lists=None,
                 last_update=None):

        self.api = api
        self.board_id = board_id

        if muted_action_types is None:
            muted_action_types = set()
        self.muted_action_types = set(muted_action_types)

        if muted_update_fields is None:
            muted_update_fields = set()
        self.muted_update_fields = set(muted_update_fields)

        if muted_update_lists is None:
            muted_update_lists = set()
        self.muted_update_lists = set(muted_update_lists)

        if last_update is None:
            last_update = arrow.now()
        self.last_update = last_update

    @classmethod
    def action_formatter(cls, action_type):
        """Returns an action formatter registering decorator."""

        def decorator(wrapped_func):
            """Associates and registers a given formatter function/action type pair."""

            cls.action_formatters[action_type] = wrapped_func

            return wrapped_func

        return decorator

    @property
    def actions(self):
        """Generator which yields any action that is eligible to be synchronized."""

        requested_action_types = set(self.action_formatters.keys()) - self.muted_action_types
        params = {
            'since': self.last_update.isoformat(),
            'filter': ','.join(requested_action_types),
            'display': 'true',
        }
        response = self.api.get(
            "/boards/{board_id}/actions".format(**self.__dict__),
            params=params,
        )
        self.last_update = arrow.now()

        # Reverse actions order to sort them chronologically
        actions = response.json()
        actions.reverse()

        for action in actions:
            if action['type'] == 'updateCard':
                for field_name in self.muted_update_fields:
                    action['data']['old'].pop(field_name, None)
                if 'listAfter' in action['data'] \
                    and action['data']['listAfter']['name'] in self.muted_update_lists:
                    continue
                if not any(action['data']['old'].keys()):
                    continue
            yield action

    def format_action(self, action):
        """Returns a human-readable representation of an action"""

        return self.action_formatters[action['type']](action)


@TrelloActivityFeed.action_formatter('createCard')
def card_create_formatter(action):
    """Formatter for the `createCard` action."""

    return "`{display[entities][memberCreator][username]}` created card " \
           "`{display[entities][card][text]}` in list " \
           "`{display[entities][list][text]}`.".format(**action)


@TrelloActivityFeed.action_formatter('moveCardToBoard')
def card_import_formatter(action):
    """Formatter for the `moveCardToBoard` action."""

    return "`{display[entities][memberCreator][username]}` imported card " \
           "`{display[entities][card][text]}` to list " \
           "`{data[list][name]}` from another board.".format(**action)


@TrelloActivityFeed.action_formatter('addMemberToCard')
def member_join_formatter(action):
    """Formatter for the `addMemberToCard` action."""

    return "`{member[username]}` joined card " \
           "`{display[entities][card][text]}`.".format(**action)


@TrelloActivityFeed.action_formatter('removeMemberFromCard')
def member_leave_formatter(action):
    """Formatter for the `removeMemberFromCard` action."""

    return "`{member[username]}` left card " \
           "`{display[entities][card][text]}`.".format(**action)


@TrelloActivityFeed.action_formatter('commentCard')
def card_comment_formatter(action):
    """Formatter for the `commentCard` action."""

    return "`{display[entities][memberCreator][username]}` commented card " \
           "`{display[entities][card][text]}`: " \
           "{display[entities][comment][text]}.".format(**action)


@TrelloActivityFeed.action_formatter('updateCheckItemStateOnCard')
def checklist_item_mark_formatter(action):
    """Formatter for the `updateCheckItemStateOnCard` action."""

    return "`{display[entities][memberCreator][username]}` marked item " \
           "`{display[entities][checkitem][text]}` as {display[entities][checkitem][state]} " \
           "in card `{display[entities][card][text]}`.".format(**action)


@TrelloActivityFeed.action_formatter('updateCard')
def card_update_formatter(action):
    """Formatter for the `updateCard` action."""

    updated_fields = list(action['data']['old'].keys())
    updated_field, dropped_fields = updated_fields[0], updated_fields[1:]
    if any(dropped_fields):  # pragma: no cover
        logging.warning('updateCard: extraneous fields dropped: %s', dropped_fields)

    output = "`{display[entities][memberCreator][username]}`"
    if updated_field == 'idList':
        output = output + " moved card `{display[entities][card][text]}` " \
            "to list `{data[listAfter][name]}`."
    else:
        updated_value = action['data']['card'][updated_field]
        output = output + " updated the card `{display[entities][card][text]}`'s" + \
            " {updated_field} to `{updated_value}`.".format(
                updated_field=updated_field,
                updated_value=updated_value,
            )

    return output.format(**action)

#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
