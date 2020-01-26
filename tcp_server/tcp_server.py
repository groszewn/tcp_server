import os
import re
import socket
from socketserver import ThreadingMixIn
from threading import Thread

from intervaltree import Interval, IntervalTree
from loguru import logger

TCP_IP = os.environ.get("HOSTNAME", "0.0.0.0")
TCP_PORT = os.environ.get("PORT", 2004)
BUFFER_SIZE = os.environ.get("BUFFER_SIZE", 20)  # Usually 1024, but we need quick response


class CustomIntervalTree(IntervalTree):
    def chop(self, begin, end, data=None):
        """
        Like remove_envelop(), but trims back Intervals hanging into
        the chopped area so that nothing overlaps.
        """
        insertions = set()
        begin = int(begin)
        end = int(end)
        begin_hits = [iv for iv in self.at(begin) if iv.begin < begin and iv.data == data]
        end_hits = [iv for iv in self.at(end) if iv.end > end and iv.data == data]
        if data:
            for iv in begin_hits:
                insertions.add(Interval(iv.begin, begin, data))
            for iv in end_hits:
                insertions.add(Interval(end, iv.end, data))
        else:
            for iv in begin_hits:
                insertions.add(Interval(iv.begin, begin, iv.data))
            for iv in end_hits:
                insertions.add(Interval(end, iv.end, iv.data))
        self.remove_envelop(begin, end, data)
        self.difference_update(begin_hits)
        self.difference_update(end_hits)
        self.update(insertions)

    def envelop(self, begin, end=None, data=None):
        """
        Returns the set of all intervals fully contained in the range
        [begin, end).
        Completes in O(m + k*log n) time, where:
          * n = size of the tree
          * m = number of matches
          * k = size of the search range
        :rtype: set of Interval
        """
        root = self.top_node
        if not root:
            return set()
        if end is None:
            iv = begin
            return self.envelop(iv.begin, iv.end)
        elif begin >= end:
            return set()
        result = root.search_point(begin, set())  # bound_begin might be greater
        boundary_table = self.boundary_table
        bound_begin = boundary_table.bisect_left(begin)
        bound_end = boundary_table.bisect_left(end)  # up to, but not including end
        result.update(
            root.search_overlap(
                # slice notation is slightly slower
                boundary_table.keys()[index]
                for index in range(bound_begin, bound_end)
            )
        )

        # TODO: improve envelop() to use node info instead of less-efficient filtering
        if data:
            result = set(
                iv for iv in result if iv.begin >= begin and iv.end <= end and iv.data == data
            )
        else:
            result = set(iv for iv in result if iv.begin >= begin and iv.end <= end)
        return result

    def remove_envelop(self, begin, end, data=None):
        """
        Removes all intervals completely enveloped in the given range.
        Completes in O((r+m)*log n) time, where:
          * n = size of the tree
          * m = number of matches
          * r = size of the search range
        """
        hitlist = self.envelop(begin, end, data)
        for iv in hitlist:
            self.remove(iv)


TREE = CustomIntervalTree()
MAX_INT = 2 ** 32 - 1


# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        logger.debug(f"[+] New server socket thread started for {ip}:{port}")

    def run(self):
        while True:
            data = self.conn.recv(2048).decode("utf-8").strip().split()
            is_valid = self.validate_data(data)
            if not is_valid:
                continue
            self.perform_action(data)

    def perform_action(self, data):
        actions = {"ADD": self.perform_add, "DEL": self.perform_delete, "FIND": self.perform_find}
        actions[data[0]](data)

    def perform_add(self, data):
        TREE[int(data[1]) : int(data[2])] = data[3]
        self.conn.send(str.encode("OK\n"))

    def perform_delete(self, data):
        if len(data) == 3:
            TREE.chop(int(data[1]), int(data[2]) + 1)
        else:
            TREE.chop(int(data[1]), int(data[2]) + 1, data[3])
        self.conn.send(str.encode("OK\n"))

    def perform_find(self, data):
        results = []
        if len(data) == 2:
            results = sorted([iv.data for iv in TREE.at(int(data[1]))])
        else:
            results = sorted([iv.data for iv in TREE.overlap(int(data[1]), int(data[2]))])
        if not results:
            self.conn.send(str.encode("ERROR no results\n"))
            return
        response = " ".join(results) + "\n"
        self.conn.send(str.encode(response))

    def validate_data(self, data):
        validator = {
            "ADD": self.validate_add,
            "DEL": self.validate_delete,
            "FIND": self.validate_find,
        }
        if len(data) == 0:
            return False
        elif validator.get(data[0]):
            return validator[data[0]](data)
        self.conn.send(str.encode("ERROR invalid command\n"))
        return False

    def validate_add(self, data):
        if len(data) != 4:
            self.conn.send(str.encode("ERROR invalid ADD command\n"))
            return False
        first_arg_valid, response = validate_numeric_arg(data[1], place="first")
        if not first_arg_valid:
            self.conn.send(response)
            return False
        second_arg_valid, response = validate_numeric_arg(data[2], place="second")
        if not second_arg_valid:
            self.conn.send(response)
            return False
        third_arg_valid = validate_text_arg(data[3])
        if not third_arg_valid:
            self.conn.send(str.encode("ERROR name arg must be a string\n"))
            return False
        return True

    def validate_delete(self, data):
        if len(data) not in (3, 4):
            self.conn.send(str.encode("ERROR invalid DEL command\n"))
            return False
        first_arg_valid, response = validate_numeric_arg(data[1], place="first")
        if not first_arg_valid:
            self.conn.send(response)
            return False
        second_arg_valid, response = validate_numeric_arg(data[2], place="second")
        if not second_arg_valid:
            self.conn.send(response)
            return False
        if len(data) > 3:
            third_arg_valid = validate_text_arg(data[3])
            if not third_arg_valid:
                self.conn.send(str.encode("ERROR name arg must be a string\n"))
                return False
        return True

    def validate_find(self, data):
        if len(data) not in (2, 3):
            self.conn.send(str.encode("ERROR invalid FIND command\n"))
            return False
        first_arg_valid, response = validate_numeric_arg(data[1], place="first")
        if not first_arg_valid:
            self.conn.send(response)
            return False
        if len(data) > 2:
            second_arg_valid, response = validate_numeric_arg(data[2], place="second")
            if not second_arg_valid:
                self.conn.send(response)
                return False
        return True


def validate_numeric_arg(data, place="first"):
    try:
        i = int(data)
        if i < 0 or i > MAX_INT:
            response = str.encode(f'ERROR invalid integer "{data}"\n')
            return False, response
    except ValueError:
        response = str.encode(f"ERROR {place} arg must be an integer\n")
        return False, response
    return True, ""


def validate_text_arg(data):
    # Check that string only made up of allowed characters
    return not re.compile(r"[^a-zA-Z0-9-_]").search(data)


def run():
    logger.info(f"TCP Server started on port {TCP_PORT}...")
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((TCP_IP, TCP_PORT))
    threads = []

    while True:
        try:
            tcp_server.listen(4)  # How large can the backlog get
            (conn, (ip, port)) = tcp_server.accept()
            newthread = ClientThread(conn, ip, port)
            newthread.start()
            threads.append(newthread)
        except KeyboardInterrupt:
            break  # Handle SIGINT from terminal

    for t in threads:
        t.join()


if __name__ == "__main__":
    run()
