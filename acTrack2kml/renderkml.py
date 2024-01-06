#! /bin/env python3

from selenium import webdriver
import time
import sys
import os
import subprocess as sp
import http.client
import logging

logger = logging.getLogger(__name__)


class RenderKML(object):

    def __init__(self):
        self.bounds = None
        self.kmlfiles = []
        self.cwd = os.getcwd()
        self.use_firefox = False
        self.http_port = 8008
        self.driver = None
        self.serverp = None

    def setFiles(self, kmlfiles):
        self.kmlfiles = kmlfiles[:]

    def setBounds(self, bounds):
        self.bounds = bounds

    def write_js(self, path=None):
        if not path:
            path = "flight_data/flight_data.js"
        with open(path, "w") as js:
            js.write('var kmlfiles=[]\n')
            for kml in self.kmlfiles:
                js.write('kmlfiles.push("%s");\n' % (kml))
            if self.bounds:
                js.write('var defaultbounds="%s";\n' % (self.bounds))

    def start_driver(self):
        driver = None
        if self.use_firefox:
            options = webdriver.FirefoxOptions()
            options.page_load_strategy = 'normal'
            args = ['--headless', '--new-instance']
            for arg in args:
                options.add_argument(arg)
            driver = webdriver.Firefox(options=options)
        else:
            # https://github.com/GoogleChrome/chrome-launcher/blob/main/docs/chrome-flags-for-tools.md
            args = ["--headless=new",
                    "--disable-extensions", "--no-first-run",
                    "--hide-scrollbars",
                    "--enable-logging=stderr", "--v=2",
                    "--disable-sync"]
            options = webdriver.ChromeOptions()
            options.page_load_strategy = 'normal'
            for arg in args:
                options.add_argument(arg)
            driver = webdriver.Chrome(options=options)
        self.driver = driver

    def dump_image(self, image):
        driver = self.driver
        driver.set_window_size(1024, 768)
        url = f'http://localhost:{self.http_port}/flight_data.html'
        logger.debug("...loading page: %s", url)
        driver.get(url)
        # selenium WebDriver has other synchronization options, but I don't
        # know how to tell when OSM is done rendering the tracks, so sticking
        # with the same fixed delay.
        time.sleep(10)
        logger.debug("...saving screenshot: %s", image)
        driver.save_screenshot(image)

    def quit_driver(self):
        self.driver.quit()
        self.driver = None

    def start_server(self):
        """
        Start simple web server for the current directory.  This works around
        CORS restrictions.
        """
        # https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Tools_and_setup/set_up_a_local_testing_server
        args = [sys.executable, '-m', 'http.server', str(self.http_port)]
        logger.info("starting http server: %s", " ".join(args))
        self.serverp = sp.Popen(args, shell=False)
        client = http.client.HTTPConnection('localhost', self.http_port,
                                            timeout=1)
        attempts = 0
        while attempts < 5:
            # just in case the server quits quickly due to something like
            # address in use, wait first before polling and connecting.
            time.sleep(1)
            if self.serverp.poll() is not None:
                sys.exit(self.serverp.returncode)
            try:
                attempts += 1
                client.connect()
                break
            except ConnectionRefusedError as ex:
                if attempts >= 5:
                    raise ex
        logger.info("server connection open...")
        client.close()

    def stop_server(self):
        logger.info("closing http server...")
        if self.serverp:
            self.serverp.kill()
        self.serverp.wait(5)

    def main(self, args):
        logger.debug("entering main...")
        kmlfiles = []
        bounds = None
        image = 'renderkml.png'
        if len(args) == 0:
            print("Usage: renderkml.py <image.png> <file.kml> [file2.kml ...] "
                  "[wlon,slat,elon,nlat]")
            sys.exit(1)
        for arg in args:
            if arg.endswith(".kml"):
                kmlfiles.append(arg)
            elif arg.endswith(".png"):
                image = arg
            else:
                bounds = arg
        self.setFiles(kmlfiles)
        self.setBounds(bounds)
        self.write_js()
        self.start_server()
        self.start_driver()
        self.dump_image(image)
        self.quit_driver()
        self.stop_server()
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    rkml = RenderKML()
    sys.exit(rkml.main(sys.argv[1:]))
