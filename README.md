# TCP Server

This package contains code necessary for spinning up a TCP server that accepts
concurrent connections and handles interval tree requests.

## Installation

This project expects that you are running at least Python 3.5.

To get up and running, you can navigate to the root of the project and simply
run

```
pip install .
```

## Starting the server

The installed python package has an `entry_point` defined for ease of use.
Simply run

```
nks_server
```

to start the server.

You can override the hostname, port, and TCP server buffer size by modifying the
following environment variables.
* `HOSTNAME` (default: `0.0.0.0`)
* `PORT` (default: `2004`)
* `BUFFER_SIZE` (default: `20`)

## Testing

All tests are contained under the `tests` folder.  You can execute the test
suite by running

```
pytest
```
