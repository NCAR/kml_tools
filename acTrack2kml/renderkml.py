#! /bin/env python3

from selenium import webdriver
import time
import sys
import os
import logging

logger = logging.getLogger(__name__)

# -77.9957, 28.9685, -74.2237, 37.1555

class RenderKML(object):

    def __init__(self):
        self.bounds = None
        self.kmlfiles = []
        self.cwd = os.getcwd()
        self.use_firefox = False

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

    def dump_image_firefox(self, image):
        options = webdriver.FirefoxOptions()
        args = ['-headless', '--new-instance', '-P', 'test', '--safe-mode']
        for arg in args:
            options.add_argument(arg)
        driver = webdriver.Firefox(executable_path="/usr/bin/firefox",
                                   firefox_options=options)
        driver.set_window_size(1024, 768) # optional
        driver.get('file://%s/flight_data.html' % (self.cwd))
        time.sleep(10)
        driver.save_screenshot(image) # save a screenshot to disk
        driver.quit()

    def dump_image(self, image):
        driver = webdriver.PhantomJS()
        driver.set_window_size(1024, 768) # optional
        driver.get('file://%s/flight_data.html' % (self.cwd))
        time.sleep(10)
        driver.save_screenshot(image) # save a screenshot to disk
        driver.quit()

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
        if self.use_firefox:
            self.dump_image_firefox(image)
        else:
            self.dump_image(image)
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rkml = RenderKML()
    sys.exit(rkml.main(sys.argv[1:]))
