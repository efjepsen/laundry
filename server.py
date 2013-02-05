#!/usr/bin/python

import os, RPi.GPIO, threading, time, web

os.chdir('/home/pi/laundry/')
RPi.GPIO.setmode(RPi.GPIO.BOARD)
web.config.smtp_server = 'outgoing.mit.edu'
web.config.debug = False

class Device:
    def __init__(self, port):
        """Create a device connected to the specified GPIO port."""
        self.port = port
        self.state, self.time = False, time.time()
        self.emails = []
        RPi.GPIO.setup(port, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)        
    def update(self):
        """Sample the GPIO port and take action as necessary."""
        # GPIO input is the inverse of machine state (i.e. False if on)
        if self.state == RPi.GPIO.input(self.port):
            self.state = not self.state
            if self.state: self.time = time.time()  # if just turned on
            else: self.notify()                     # if just turned off
    def get_time(self):
        """Get the number of minutes since the machine last turned on."""
        return (time.time() - self.time) / 60
    def add_email(self, email):
        """Add an email address to be notified when the machine turns off."""
        print(self.emails)
        self.emails.append(email)
    def notify(self):
        """Notify email addresses that the machine has turned off."""
        for email in self.emails:
            try:
                web.sendmail('clothes@mit.edu', email,
                             '{} is done'.format(self.name),
                             'Your laundry took {:.1f} minutes.'
                             .format(self.get_time()))
            except: pass
    def __str__(self):
        """Format a string suitable for display in HTML."""
        self.update()
        return ('on for {:.0f} min'.format(self.get_time())
                if self.state else 'not in use')

devices = {'Mr. Washer': Device(21),  # GPIO9
           'Mrs. Washer': Device(22),  # GPIO25
           'Mr. Dryer': Device(23),  # GPIO11
           'Mrs. Dryer': Device(24)}  # GPIO8
for name in devices: devices[name].name = name

urls = ('/', 'Server', '/notify', 'Server')

class Server:
    def GET(self):
        return web.template.render('.').index(devices)
    def POST(self):
        data = web.input(devices=[])
        for name in data.devices:
            devices[name].add_email(data.email)
        raise web.seeother('/')

# spin off a thread to call update() in the background
def monitor():
    while True:
        for name in devices:
            devices[name].update()
        time.sleep(1)
thread = threading.Thread(target=monitor)
thread.daemon = True
thread.start()

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
