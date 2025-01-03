import configparser
import sys
import pathlib

config = configparser.ConfigParser()
config.sections()
config.read(f'{pathlib.Path(__file__).parent.resolve()}/config.cfg')
