from configparser import ConfigParser
from pathlib import Path

class Config:
    def __init__(self):
        self._config = ConfigParser()
        if not Path('options.ini').exists():
            self._create_default()
        self._config.read('options.ini')

    @property
    def directory(self) -> Path:
        to_return = self._config.get('files', 'Directory', fallback='None')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def queue_type(self) -> str:
        return self._config.get('files', 'Queue_Type', fallback='File')

    @property
    def enqueue_existing(self) -> bool:
        return self._config.getboolean('files','Enqueue_Existing', fallback=False)

    @property
    def image_format(self) -> str:
        return self._config.get('images','Image_Format',fallback='CZI')

    @property
    def white_point(self) -> int:
        return self._config.getint('images', 'White_Point', fallback=4095)

    @property
    def scaling(self) -> float:
        return self._config.getfloat('images', 'Scaling', fallback=3.45)

    @property
    def max_radius(self) -> int:
        return self._config.getint('images', 'Max_Radius', fallback = 2500)

    @property
    def masking_method(self) -> str:
        return self._config.get('advanced', 'Masking_Method', fallback='Thresholding')

    @property
    def normalization(self) -> bool:
        return self._config.getboolean('advanced', 'Normalization', fallback=True)

    @property
    def normalization_percentile(self) -> float:
        return self._config.getfloat('advanced', 'Normalization_Percentile', fallback=95.0)

    @property
    def threshold_level(self) -> int:
        return self._config.getint('advanced', 'Threshold_Level', fallback=100)

    @property
    def radius_method(self) -> str:
        return self._config.get('advanced', 'Radius_Method', fallback='Contour')

    @property
    def required_stable(self) -> int:
        return self._config.getint('advanced', 'Required_Stable', fallback=3)

    @property
    def check_delay(self) -> float:
        return self._config.getfloat('advanced', 'Check_Delay', fallback=0.2)

    @property
    def max_checks(self) -> int:
        return self._config.getint('advanced', 'Max_Checks', fallback=10)

    def _create_default(self):
        with open('options.ini', 'w') as config_file:
            self._config['files'] = {'Directory': 'None',
                                     'Queue_Type': 'File',
                                     'Enqueue_Existing': 'False'}
            self._config['images'] = {'Image_Format': 'CZI',
                                        'White_Point': '4095',
                                        'Scaling': '3.45',
                                        'Max_Radius': '2500'}
            self._config['advanced'] = {'Masking_Method': 'Thresholding',
                                        'Normalization': 'True',
                                        'Normalization_Percentile': '95.0',
                                        'Threshold_Level': '100',
                                        'Radius_Method': 'Contour',
                                        'Required_Stable': '3',
                                        'Check_Delay': '0.2',
                                        'Max_Checks': '10'}
            self._config.write(config_file)

    def save(self) -> None:
        with open('options.ini', 'w') as config_file:
            self._config.write(config_file)

    def set(self, section: str, option: str, value: str|int|float|bool) -> None:
        if section not in self._config:
            return
        self._config.set(section, option, str(value))

