'''
http stuff via twisted
'''

import sys
import time
import pprint
import traceback

from twisted.internet import reactor
from twisted.internet import task

from twisted.web import server
from twisted.web.resource import Resource

from ggplib.symbols import SymbolFactory, ListTerm
from ggplib.player import match

from ggplib.util import log

symbol_factory = SymbolFactory()

# timeout if we don't hear anything for at least this time
GAMESERVER_TIMEOUT = 60 * 20

###############################################################################


class GGPServer(Resource):
    ''' a server deal withs the ggp web service like protocol.  It has only one player, which is
      passed into each new match. '''

    current_match = None
    player = None
    last_info_time = 0
    info_counts = 0

    timeout_deferred = None

    def set_player(self, player):
        self.player = player

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        log.debug("Got GET request from: %s" % request.getClientIP())
        return self.handle(request)

    def render_POST(self, request):
        #log.debug("Got POST request from: %s" % request.getClientIP())
        #log.debug("HEADERS : %s" % pprint.pformat(request.getAllHeaders()))

        res = self.handle(request)
        res = res.replace('(',' ( ').replace(')',' ) ')

        # 'CORS' - stuff I don't understand.  Was needed to run standford 'player checker'.
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers',
                          'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', 2520)
        request.setHeader('Content-type', 'application/json')

        return res

    def handle(self, request):
        content = request.content.getvalue()

        # Tiltyard seems to ping with empty content...
        if content == "":
            return self.handle_info()

        try:
            symbols = list(symbol_factory.symbolize(content))

            # get head
            if len(symbols) == 0:
                log.warning('Empty symbols')
                return self.handle_info()

            head = symbols[0]
            if head.lower() == "info":
                return self.handle_info()

            elif head.lower() == "start":
                log.debug("HEADERS : %s" % pprint.pformat(request.getAllHeaders()))
                log.debug(str(symbols))
                return self.handle_start(symbols)

            elif head.lower() == "play":
                log.debug(str(symbols))
                return self.handle_play(symbols)

            elif head.lower() == "stop":
                log.debug(str(symbols))
                return self.handle_stop(symbols)

            elif head.lower() == "abort":
                log.debug(str(symbols))
                return self.handle_abort(symbols)

            else:
                log.error("UNHANDLED REQUST %s" % symbols)

        except Exception, exc:
            log.error("ERROR - aborting: %s" % exc)
            type, value, tb = sys.exc_info()
            log.error(traceback.format_exc())

            if self.current_match:
                self.current_match.do_abort()
                self.current_match = None

            return "aborted"

    def handle_info(self):
        t = time.time()
        # do info_counts or we get reports of "0 infos in the last minute"
        self.info_counts += 1
        if t - self.last_info_time > 60:
            log.debug("Got %s infos in last minute" % self.info_counts)
            self.info_counts = 0
            self.last_info_time = t

        if self.current_match is None:
            return "((name %s) (status available))" % self.player.get_name()
        else:
            return "((name %s) (status busy))" % self.player.get_name()

    def handle_start(self, symbols):
        assert len(symbols) == 6
        match_id = symbols[1]
        role = symbols[2]
        gdl = symbols[3]
        meta_time = int(symbols[4])
        move_time = int(symbols[5])

        if self.current_match is not None:
            log.debug("GOT A START message for %s while already playing match" % match_id)
            return "busy"
        else:
            log.debug("Starting new match %s" % match_id)
            self.current_match = match.Match(match_id, role, meta_time, move_time, self.player, gdl)
            try:
                # start gameserver timeout
                self.update_gameserver_timeout(self.current_match.meta_time)

                self.current_match.do_start()
                return "ready"

            except match.BadGame:
                return "busy"

    def handle_play(self, symbols):
        assert len(symbols) == 3
        match_id = symbols[1]
        if self.current_match is None:
            log.warning("rx'd play for non-current match %s" % match_id)
            return "busy"
        if self.current_match.match_id != match_id:
            log.error("rx'd play different from current match (%s != %s)" % (match_id, self.current_match.match_id))
            return "busy"

        move = symbols[2]

        if isinstance(move, ListTerm):
            move = list(move)
        else:
            assert move.lower() == 'nil', "Move is %s" % move
            move = None

        # update gameserver timeout
        self.update_gameserver_timeout(self.current_match.move_time)
        return self.current_match.do_play(move)

    def handle_stop(self, symbols):
        assert len(symbols) == 3
        match_id = symbols[1]
        if self.current_match is None:
            log.warning("rx'd 'stop' for non-current match %s" % match_id)
            return "busy"
        if self.current_match.match_id != match_id:
            log.error("rx'd 'stop' different from current match (%s != %s)" % (match_id, self.current_match.match_id))
            return "busy"

        move = symbols[2]

        # XXX bug with standford 'player checker'??? XXX need to find out what is going on here?
        if isinstance(move, str) and move.lower != "nil":
            move = symbol_factory.symbolize("( %s )" % move)

        res = self.current_match.do_play(move)
        if res != "done":
            log.error("WTF game not done %s" % self.sm)
        else:

            # cancel any timeout callbacks
            self.update_gameserver_timeout(None)

            self.current_match.do_stop()

        self.current_match = None

        return "done"

    def handle_abort(self, symbols):
        assert len(symbols) == 2
        match_id = symbols[1]

        if self.current_match is None:
            log.warning("rx'd 'abort' for non-current match %s" % match_id)
            return "busy"

        if self.current_match.match_id != match_id:
            log.error("rx'd 'abort' different from current match (%s != %s)" % (match_id, self.current_match.match_id))
            return "busy"

        # cancel any timeout callbacks
        self.update_gameserver_timeout(None)

        res = self.current_match.do_abort()
        self.current_match = None

        return res

    def update_gameserver_timeout(self, wait_time):
        # cancel the current timeout
        if self.timeout_deferred is not None:
            self.timeout_deferred.cancel()
            self.timeout_deferred = None

        if wait_time is not None:
            when_time = wait_time + GAMESERVER_TIMEOUT
            self.timeout_deferred = task.deferLater(reactor, when_time, self.gameserver_timeout)

    def gameserver_timeout(self):
        log.critical("Timeout from server - forcing aborting")

        if self.current_match:
            self.current_match.do_abort()
            self.current_match = None

        self.timeout_deferred = None

###############################################################################

def main():
    from ggplib.player.get import get_player

    port = int(sys.argv[1])
    player_type = sys.argv[2]

    # if third argument, set to player name
    try:
        player_name = sys.argv[3]
    except IndexError:
        player_name = player_type

    from ggplib import interface
    interface.initialise_k273(1, log_name_base=player_name)
    log.initialise()

    log.info("Running player '%s' on port %d" % (player_type, port))
    player = get_player(player_type, player_name)

    ggp = GGPServer()
    ggp.set_player(player)
    site = server.Site(ggp)

    reactor.listenTCP(port, site)
    reactor.run()

if __name__ == "__main__":
    main()
