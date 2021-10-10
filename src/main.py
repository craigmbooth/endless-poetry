import time

import network
import machine

import font_title, font_body
from inkplate10 import Inkplate
from secrets import ssid, password
import urequests
import writer

START_TIME = time.time()

# The number of seconds to wait between refreshing the page
DELAY_TIME_S = 300

def log(message):
    """Utility function adds elapsed time to the start of `message` before printing
    it
    """
    elapsed = time.time() - START_TIME
    print("{elapsed}: {message}".format(elapsed=elapsed, message=message))


def connect_network():
    """Connect to the wifi network specified by ssid and password"""

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        log("connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    log("connected to network with IP %s" % sta_if.ifconfig()[0])

class Poem:
    """Class represents a poem and provides a few useful constants related to it"""

    def __init__(self, title: str, author: str, content: str) -> None:
        self.title = title
        self.author = author
        self.content = content
        self.lines = self.content.split("\n")
        self.num_lines = len(self.lines)
        self.max_line_length = max([len(l) for l in self.lines])
        log("Instantiated poem %s by %s" % (title, author))

    def render(self, display, page: int) -> None:

        # A little hacky, but the following geometric constants place things on the
        # page
        left_margin = 40
        top_margin = 40
        header_height = 120
        line_spacing = 15

        # x-offset for all lines on this page
        xoff = int(page * display.width()/2 + left_margin)

        # Display an approximately 2/3 width line under the title
        display.drawLine(xoff, header_height,
                        xoff + 400, header_height,
                        display.BLACK)

        # Calculate how many blank lines to leave to get the poem vertically centered
        max_lines = (display.height()-header_height) / line_spacing
        skip_lines = int((max_lines - self.num_lines)/2)

        title_writer = writer.Writer(display, font_title, verbose=False)
        body_writer = writer.Writer(display, font_body, verbose=False)

        # Write the header
        title_writer.set_textpos(display, top_margin, xoff)
        title_writer.printstring(self.title)
        body_writer.set_textpos(display, top_margin+50, xoff)
        body_writer.printstring(self.author)

        # Write the poem
        yoff = header_height + skip_lines * line_spacing
        for x in self.lines:
            body_writer.set_textpos(display, yoff, xoff)
            body_writer.printstring(x)
            yoff += line_spacing

class Poet:
    """The Poet class has a "speak" generator function, which creates an infinite
    iterator over poems on the poemist API
    """

    # Endpoint to GET poems from
    url = "https://www.poemist.com/api/v1/randompoems"


    def __init__(self):
        """Instantiating a Poet will cause it to `speak` two random poems, write
        them to the book, and then exit
        """
        connect_network()
        self.display = Inkplate(Inkplate.INKPLATE_1BIT)
        self.display.begin()
        self.display.clearDisplay()
        poem = next(self.speak())
        poem.render(self.display, 0)
        poem = next(self.speak())
        poem.render(self.display, 1)
        self.display.display()
        time.sleep(10)
        machine.deepsleep(1000*DELAY_TIME_S)

    def speak(self): # -> Generator[Poem]   (no typing module on micropython)
        """yield a random Poem object"""

        while True:

            log("Making get request to %s" % self.url)
            response = urequests.get(self.url)

            try:
                result = response.json()
            except ValueError:
                # If things fail, print the full response and wait 5 minutes
                print(response)
                print(response.content)
                time.sleep(300)
                continue

            for poem_payload in result:

                poem = Poem(poem_payload["title"],
                            poem_payload["poet"]["name"],
                            poem_payload["content"])

                # The following is a little hacky, but filter out poems that wont display
                # well on the epaper display due to number of lines, line length,
                # long title or presence of unicode characters.

                if poem.content is None:
                    continue

                if not all(ord(c) < 128 for c in poem.content):
                    log("Skipping poem {title}, contains unicode".format(
                        title=poem.title))

                if poem.num_lines > 45:
                    log("Skipping poem {title}, too many lines ({num_lines})".format(
                       title=poem.title, num_lines=poem.num_lines))
                    continue

                if poem.max_line_length > 75:
                    log("Skipping poem {title}, long lines ({max_line_length})".format(
                       title=poem.title, max_line_length=poem.max_line_length))
                    continue

                if len(poem.title) > 40:
                    log("Skipping poem {title}, long title".format(
                       title=poem.title))
                    continue

                yield poem

            # Additional sleep here.  In the rare case that we reject 5 consecutive poems,
            # ensure that there is some space before making another API request
            time.sleep(10)


Poet()

