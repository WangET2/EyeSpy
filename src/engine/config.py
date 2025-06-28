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
    def write_roi(self) -> bool:
        return self._config.getboolean('files', 'Write_ROI', fallback=False)

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
        return self._config.get('processing', 'Masking_Method', fallback='Thresholding')

    @property
    def normalization(self) -> bool:
        return self._config.getboolean('processing', 'Normalization', fallback=True)

    @property
    def normalization_percentile(self) -> float:
        return self._config.getfloat('processing', 'Normalization_Percentile', fallback=99.5)

    @property
    def threshold_level(self) -> int:
        return self._config.getint('processing', 'Threshold_Level', fallback=1526)

    @property
    def radius_method(self) -> str:
        return self._config.get('processing', 'Radius_Method', fallback='Contour')

    @property
    def required_stable(self) -> int:
        return self._config.getint('processing', 'Required_Stable', fallback=3)

    @property
    def check_delay(self) -> float:
        return self._config.getfloat('processing', 'Check_Delay', fallback=0.2)

    @property
    def max_checks(self) -> int:
        return self._config.getint('processing', 'Max_Checks', fallback=10)

    @property
    def training_directory(self) -> Path:
        to_return = self._config.get('bayesian', 'Training_Directory', fallback='None')
        return Path(to_return) if to_return.lower() != 'none' else None

    @property
    def testing_directory(self) -> Path:
        to_return = self._config.get('bayesian', 'Testing_Directory', fallback = 'None')
        return Path(to_return) if to_return.lower() != 'none' else None

    def _create_default(self):
        with open('options.ini', 'w') as config_file:
            self._config['files'] = {'Directory': 'None',
                                     'Queue_Type': 'File',
                                     'Enqueue_Existing': 'False',
                                     'Write_ROI': 'False'}
            self._config['images'] = {'Image_Format': 'CZI',
                                        'White_Point': '4095',
                                        'Scaling': '3.45',
                                        'Max_Radius': '2500'}
            self._config['processing'] = {'Masking_Method': 'Thresholding',
                                        'Normalization': 'True',
                                        'Normalization_Percentile': '99.5',
                                        'Threshold_Level': '1526',
                                        'Radius_Method': 'Eigenvalue',
                                        'Required_Stable': '3',
                                        'Check_Delay': '0.2',
                                        'Max_Checks': '10'}
            self._config['bayesian'] = {'Training_Directory': 'None',
                                        'Testing_Directory': 'None'}
            self._config.write(config_file)

    def save(self) -> None:
        with open('options.ini', 'w') as config_file:
            self._config.write(config_file)

    def set(self, section: str, option: str, value: str|int|float|bool) -> None:
        if section not in self._config:
            return
        self._config.set(section, option, str(value))

    def reset(self) -> None:
        self._create_default()

    def validate(self) -> None:
        if not self._config.get('images', 'White_Point').isdigit():
            raise ValueError('Image White Point must be an integer value.')
        if not self._config.get('images', 'Scaling').replace('.','',1).isdigit():
            raise ValueError('Image Scaling must be a numeric value.')
        if not self._config.get('images', 'Max_Radius').isdigit():
            raise ValueError('Maximum ROI Radius must be an integer value.')
        if not self._config.get('processing', 'Normalization_Percentile').replace('.','',1).isdigit():
            raise ValueError('Normalization Percentile must be a numeric value.')
        if not self._config.get('processing','Threshold_Level').isdigit():
            raise ValueError('Threshold Intensity must be an integer value.')
        if not self._config.get('processing', 'Required_Stable').isdigit():
            raise ValueError('Stability Checks must be an integer value.')
        if not self._config.get('processing', 'Check_Delay').replace('.','',1).isdigit():
            raise ValueError('Delay Between Stability Checks must be a numeric value.')
        if not self._config.get('processing', 'Max_Checks').isdigit():
            raise ValueError('Maximum Stability Checks must be an integer value.')
            