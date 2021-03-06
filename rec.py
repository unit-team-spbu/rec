import json
from nameko.rpc import rpc
from nameko.rpc import RpcProxy
from nameko.timer import timer
from nameko.web.handlers import http
import config as cfg
from datetime import timedelta, datetime
from time import sleep


class REC:
    """Microservice for requesting events from every crawler"""
    # Vars

    name = "raw_events_collector"
    # Crawlers-----------------------------------
    # TODO : find a way to inject crawlers via some updatable config
    it_events_rpc = RpcProxy('it_events_crawler')
    softline_rpc = RpcProxy('softline_crawler')
    it_world_rpc = RpcProxy('it_world_crawler')
    # --------------------------------------------
    preh_rpc = RpcProxy('primary_raw_events_handler')
    logger_rpc = RpcProxy('logger')

    # Logic

    def _update_crawlers(self):
        """Updating crawlers list
            (Is not used now due to inability to run crawlers dynamically)"""
        self.crawlers_rpc = list()
        for crawler in cfg.CRAWLERS:
            self.crawlers_rpc.append(RpcProxy(crawler))

    # API

    @rpc
    def update(self):
        """Requests crawlers for events
        :param now: flag for instant service launch (we don't wait for cfg.TIME)
        :returns a batch with all events"""
        get_res = list()
        events = list()

        # requesting events from each crawler------------------------------
        try:
            get_res.append(self.it_events_rpc.get_upcoming_events.call_async())
        except:
            self.logger_rpc.log(self.name, self.update.__name__, None, "Error", "it_events crawler doesn't work")
        try:
            get_res.append(self.softline_rpc.get_upcoming_events.call_async())
        except:
            self.logger_rpc.log(self.name, self.update.__name__, None, "Error", "Softline crawler doesn't work")
        try:
            get_res.append(self.it_world_rpc.get_upcoming_events.call_async())
        except:
            self.logger_rpc.log(self.name, self.update.__name__, None, "Error", "It world crawler doesn't work")
        # Needs to be changed with every new crawler-----------------------
        
        self.logger_rpc.log(self.name, self.update.__name__, None, "Info", "Starting fetching events...")
        print("Fetching data...")
        # getting results
        count = 1
        for res in get_res:
            events += res.result()
            print(f"[{count}/{len(get_res)}] crawlers ready")
            count += 1

        try:
            self.preh_rpc.receive_events(events)
            self.logger_rpc.log(self.name, self.update.__name__, None, "Info", "Events received and sent to preh")
        except:
            self.logger_rpc.log(self.name, self.update.__name__, None, "Error", "Can't send events from rec to preh")

        return events

    @http('GET', '/events')
    def force_update_handler(self, request):
        self.logger_rpc.log(self.name, self.force_update_handler.__name__, str(request), "Info", "Force update")

        return (200, json.dumps(self.update(), ensure_ascii=False))

    # TODO: ensure it works @MaxKuznets0v
    @timer(interval=cfg.TIMER, eager=True)
    def handle_update(self):
        """Waiting for update time and calling update"""
        now = datetime.now().time()
        if now < cfg.TIME:
            delta = timedelta(hours=(cfg.TIME.hour - now.hour),
                              minutes=(cfg.TIME.minute - now.minute),
                              seconds=(cfg.TIME.second - now.second))
        elif now > cfg.TIME:
            delta = timedelta(hours=(24 - now.hour + cfg.TIME.hour),
                              minutes=(-now.minute + cfg.TIME.minute),
                              seconds=(-now.second + cfg.TIME.second))
        print(f"Waiting {delta} ...")
        self.logger_rpc.log(self.name, self.handle_update.__name__, None, "Info", f"Waiting {delta}...")
        sleep(delta.total_seconds())
        self.logger_rpc.log(self.name, self.handle_update.__name__, None, "Info", "Daily update")
        return self.update()
