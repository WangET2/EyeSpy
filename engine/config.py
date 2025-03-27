# TODO
# Add proper config file handling
# Interface with gui.config_gui

import os
from configparser import ConfigParser

class Config:
    def __init__(self):
        if not 'options.ini' in os.listdir():
            config = ConfigParser()
            with open('options.ini', 'w') as configfile:
                config['DEFAULT'] = {'Directory': 'None',
                                     'Scaling': '5',
                                     'White Point': '128'}
                config['ADVANCED'] = {'Threshold': '100'}
                config.write(configfile)
        self.update()

    @property
    def directory(self):
        return self._directory

    @property
    def scaling(self):
        return self._scaling

    @property
    def white_point(self):
        return self._white_point

    @property
    def threshold(self):
        return self._threshold
        
    def update(self):
        config = ConfigParser()
        config.read('options.ini')
        self._directory = config['DEFAULT']['Directory']
        self._scaling = config['DEFAULT']['Scaling']
        self._white_point = config['DEFAULT']['WhitePoint']
        self._threshold = config['ADVANCED']['Threshold']

