"""Sibling subcommand modules for ticket.py.

Every module here except this file defines register(sub, t): `sub` is the argparse
subparsers object (add_parser adds --root and rejects name clashes), `t` is the ticket
module. Modules never import ticket.py. Mutations go through t.require_main_checkout
and t.commit_ticket_change; raise t.TicketError for user errors.
"""
