#!/usr/bin/env python

"""Tests for `tcp_server` package."""


import unittest

import mock

from tcp_server import tcp_server
from intervaltree import Interval


class TestSolution(unittest.TestCase):
    """Tests for `tcp_server` package."""

    def setUp(self):
        tcp_server.TREE = tcp_server.CustomIntervalTree()
        mock.patch("tcp_server.socket.socket")
        self.thread = tcp_server.ClientThread(mock.Mock(), "localhost", 2004)
        """Set up test fixtures, if any."""

    def tearDown(self):
        tcp_server.TREE = tcp_server.CustomIntervalTree()
        """Tear down test fixtures, if any."""

    def test_validate_numeric_arg_failure_invalid_integer(self):
        """
        Pass in failing numeric arguments (outside of bounds)
        """
        assert tcp_server.validate_numeric_arg(4294967296) == (
            False,
            str.encode('ERROR invalid integer "4294967296"\n'),
        )

        assert tcp_server.validate_numeric_arg(-1) == (
            False,
            str.encode('ERROR invalid integer "-1"\n'),
        )

    def test_validate_numeric_arg_failure_noninteger(self):
        """
        Pass in failing non-numeric arguments
        """
        assert tcp_server.validate_numeric_arg("blah") == (
            False,
            str.encode("ERROR first arg must be an integer\n"),
        )
        assert tcp_server.validate_numeric_arg("blah", "second") == (
            False,
            str.encode("ERROR second arg must be an integer\n"),
        )

    def test_validate_numeric_arg_success(self):
        """
        Pass in valid numeric argument
        """
        assert tcp_server.validate_numeric_arg(1) == (True, "")

    def test_validate_text_arg_failure(self):
        """
        Pass in invalid text argument
        """
        assert tcp_server.validate_text_arg("bad arg with spaces") is False

    def test_validate_text_arg_success(self):
        """
        Pass in valid text argument
        """
        assert tcp_server.validate_text_arg("goodarg") is True

    def test_validate_add_invalid_num_args(self):
        """
        Pass in too many/few arguments
        """
        assert self.thread.validate_add("ADD 1 2 3 4") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid ADD command\n"))
        assert self.thread.validate_add("ADD 1 2") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid ADD command\n"))

    def test_validate_add_invalid_first_arg(self):
        """
        Pass in bad first argument
        ."""
        data = "ADD one 2 three".split()
        assert self.thread.validate_add(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR first arg must be an integer\n"))

    def test_validate_add_invalid_second_arg(self):
        """
        Pass in bad second argument
        """
        data = "ADD 1 two three".split()
        assert self.thread.validate_add(data) is False
        self.thread.conn.send.assert_called_with(
            str.encode("ERROR second arg must be an integer\n")
        )

    def test_validate_add_invalid_third_arg(self):
        """
        Pass in bad third argument
        """
        data = "ADD 1 2 badvar!".split()
        assert self.thread.validate_add(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR name arg must be a string\n"))

    def test_validate_add_success(self):
        """
        Pass in valid arguments
        """
        data = "ADD 1 2 goodvar".split()
        assert self.thread.validate_add(data) is True
        assert self.thread.conn.send.call_count == 0

    def test_validate_delete_invalid_num_args(self):
        """
        Pass in too many/few arguments
        """
        assert self.thread.validate_delete("DEL 1 2 3 4") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid DEL command\n"))
        assert self.thread.validate_delete("DEL 1") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid DEL command\n"))

    def test_validate_delete_invalid_first_arg(self):
        """
        Pass in bad first argument
        ."""
        data = "DEL one 2 three".split()
        assert self.thread.validate_delete(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR first arg must be an integer\n"))

    def test_validate_delete_invalid_second_arg(self):
        """
        Pass in bad second argument
        """
        data = "DEL 1 two three".split()
        assert self.thread.validate_delete(data) is False
        self.thread.conn.send.assert_called_with(
            str.encode("ERROR second arg must be an integer\n")
        )

    def test_validate_delete_invalid_third_arg(self):
        """
        Pass in bad third argument
        """
        data = "DEL 1 2 badvar!".split()
        assert self.thread.validate_delete(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR name arg must be a string\n"))

    def test_validate_del_success(self):
        """
        Pass in valid arguments
        """
        data = "DEL 1 2 goodvar".split()
        assert self.thread.validate_delete(data) is True
        assert self.thread.conn.send.call_count == 0

    def test_validate_find_invalid_num_args(self):
        """
        Pass in too many/few arguments
        """
        assert self.thread.validate_find("FIND 1 2 3 4") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid FIND command\n"))
        assert self.thread.validate_find("FIND") is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid FIND command\n"))

    def test_validate_find_invalid_first_arg(self):
        """
        Pass in bad first argument
        ."""
        data = "FIND one 2".split()
        assert self.thread.validate_find(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR first arg must be an integer\n"))

    def test_validate_find_invalid_second_arg(self):
        """
        Pass in bad second argument
        """
        data = "FIND 1 two".split()
        assert self.thread.validate_find(data) is False
        self.thread.conn.send.assert_called_with(
            str.encode("ERROR second arg must be an integer\n")
        )

    def test_validate_find_success(self):
        """
        Pass in valid arguments
        """
        data = "FIND 1 2".split()
        assert self.thread.validate_find(data) is True
        assert self.thread.conn.send.call_count == 0

    def test_validate_data_invalid_num_args(self):
        """
        Pass in too few arguments
        """
        data = "".split()
        assert self.thread.validate_data(data) is False

    def test_validate_data_invalid_command(self):
        """
        Pass in a bad command argument
        """
        data = "BLAH 1 2 var".split()
        assert self.thread.validate_data(data) is False
        self.thread.conn.send.assert_called_with(str.encode("ERROR invalid command\n"))

    def test_validate_data_success(self):
        data = "ADD 1 2 x".split()
        assert self.thread.validate_data(data) is True
        data = "DEL 1 2".split()
        assert self.thread.validate_data(data) is True
        data = "FIND 1".split()
        assert self.thread.validate_data(data) is True

    def test_perform_add(self):
        data = "ADD 1 2 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 2, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))

    def test_perform_delete_entire_entry(self):
        data = "ADD 1 2 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 2, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "DEL 1 2 x".split()
        self.thread.perform_delete(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))

    def test_perform_delete_partial_entry(self):
        data = "ADD 1 5 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 5, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "DEL 2 3 x".split()
        self.thread.perform_delete(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree(
            [Interval(1, 2, "x"), Interval(4, 5, "x")]
        )
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))

    def test_perform_delete_named_delete(self):
        data = "ADD 1 5 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 5, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "ADD 1 5 y".split()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree(
            [Interval(1, 5, "x"), Interval(1, 5, "y")]
        )
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "DEL 1 5 x".split()
        self.thread.perform_delete(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 5, "y")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))

    def test_perform_find_no_results(self):
        data = "FIND 1".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_find(data)
        self.thread.conn.send.assert_called_with(str.encode("ERROR no results\n"))

    def test_perform_find_specific_number(self):
        data = "ADD 1 5 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 5, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "ADD 5 10 y".split()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree(
            [Interval(1, 5, "x"), Interval(5, 10, "y")]
        )
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "FIND 3".split()
        self.thread.perform_find(data)
        self.thread.conn.send.assert_called_with(str.encode("x\n"))

    def test_perform_find_specific_range(self):
        data = "ADD 1 5 x".split()
        assert tcp_server.TREE == tcp_server.CustomIntervalTree()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree([Interval(1, 5, "x")])
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "ADD 5 10 y".split()
        self.thread.perform_add(data)
        assert tcp_server.TREE == tcp_server.CustomIntervalTree(
            [Interval(1, 5, "x"), Interval(5, 10, "y")]
        )
        self.thread.conn.send.assert_called_with(str.encode("OK\n"))
        data = "FIND 2 7".split()
        self.thread.perform_find(data)
        self.thread.conn.send.assert_called_with(str.encode("x y\n"))
