"""Const helpers of Epson projector module."""

HTTP = "http"
TCP = "tcp"
SERIAL = "serial"
HTTP_OK = 200

TCP_PORT = 3629
TCP_SERIAL_PORT = 3620
HTTP_PORT = 80
EEMP0100 = "45454d5030313030"
SERIAL_COMMAND = "0000000002000000"
SERIAL_BYTE = bytearray.fromhex(f"{EEMP0100}{SERIAL_COMMAND}")

ACCEPT_ENCODING = "gzip, deflate"
ACCEPT_HEADER = "application/json, text/javascript"
JSON_QUERY = "json_query"
DIRECT_SEND = "directsend"

ESCVPNET_HELLO_COMMAND = "ESC/VP.net\x10\x03\x00\x00\x00\x00"
ESCVPNETNAME = "ESC/VP.net"
ESCVPNAME = "ESC/VP"
ERROR = "ERR"
PWR_ON_STATE = "01"
PWR_OFF_STATE = "04"
ESCVP_HELLO_COMMAND = "\r"
COLON = ":"
CR = "\r"
CR_COLON = CR + COLON
GET_CR = "?" + CR

POWER = "PWR"
CMODE = "CMODE"
SOURCE = "SOURCE"
VOLUME = "VOLUME"
MUTE = "MUTE"
VOL_UP = "VOL_UP"
VOL_DOWN = "VOL_DOWN"
PLAY = "PLAY"
PAUSE = "PAUSE"
FAST = "FAST"
BACK = "BACK"
TURN_ON = "PWR ON"
PWR_ON = "PWR ON"
TURN_OFF = "PWR OFF"
PWR_OFF = "PWR OFF"
ALL = "ALL"
IMGPROC_FINE = "IMGPROC_FINE"
IMGPROC_FAST = "IMGPROC_FAST"
IMGPROC = "IMGPROC"
LUMINANCE = "LUMINANCE"
MEMORY_1 = "MEMORY_1"
MEMORY_2 = "MEMORY_2"
MEMORY_3 = "MEMORY_3"
MEMORY_4 = "MEMORY_4"
MEMORY_5 = "MEMORY_5"
MEMORY_6 = "MEMORY_6"
MEMORY_7 = "MEMORY_7"
MEMORY_8 = "MEMORY_8"
MEMORY_9 = "MEMORY_9"
MEMORY_10 = "MEMORY_10"
SNO = "SNO"
BUSY = 2

LENS_MEMORY = "POPLP"
LASER_LEVEL = "LUMLEVEL"

EPSON_CODES = {"PWR": "01"}

EPSON_KEY_COMMANDS = {
    "PWR ON": [("PWR", "ON")],
    "PWR OFF": [("PWR", "OFF")],
    # "HDMILINK": [("jsoncallback", "HDMILINK?")],
    # "PWR": [("jsoncallback", "PWR?")],
    # "SOURCE": [("jsoncallback", "SOURCE?")],
    # "CMODE": [("jsoncallback", "CMODE?")],
    # "VOLUME": [("jsoncallback", "VOL?")],
    "CMODE_AUTO": [("CMODE", "00")],
    "CMODE_CINEMA": [("CMODE", "15")],
    "CMODE_NATURAL": [("CMODE", "07")],
    "CMODE_BRIGHT": [("CMODE", "0C")],
    "CMODE_DYNAMIC": [("CMODE", "06")],
    "CMODE_3DDYNAMIC": [("CMODE", "18")],
    "CMODE_3DCINEMA": [("CMODE", "17")],
    "CMODE_3DTHX": [("CMODE", "19")],
    "CMODE_BWCINEMA": [("CMODE", "20")],
    "CMODE_ARGB": [("CMODE", "21")],
    "CMODE_DCINEMA": [("CMODE", "22")],
    "CMODE_THX": [("CMODE", "13")],
    "CMODE_GAME": [("CMODE", "0D")],
    "CMODE_STAGE": [("CMODE", "16")],
    "CMODE_AUTOCOLOR": [("CMODE", "C1")],
    "CMODE_XV": [("CMODE", "0B")],
    "CMODE_THEATRE": [("CMODE", "05")],
    "CMODE_THEATREBLACK": [("CMODE", "09")],
    "CMODE_THEATREBLACK2": [("CMODE", "0A")],
    "CMODE_VIVID": [("CMODE", "23")],
    "VOL_UP": [("KEY", "56")],
    "VOL_DOWN": [("KEY", "57")],
    "MUTE": [("KEY", "D8")],
    "HDMI1": [("KEY", "4D")],
    "HDMI2": [("KEY", "40")],
    "PC": [("KEY", "44")],
    "VIDEO": [("KEY", "46")],
    "USB": [("KEY", "85")],
    "LAN": [("KEY", "53")],
    "WFD": [("KEY", "56")],
    "PLAY": [("KEY", "D1")],
    "PAUSE": [("KEY", "D3")],
    "STOP": [("KEY", "D2")],
    "BACK": [("KEY", "D4")],
    "FAST": [("KEY", "D5")],
    "IMGPROC_FINE": [("IMGPROC", "01")],
    "IMGPROC_FAST": [("IMGPROC", "02")],
    "LUMINANCE_ECO": [("LUMINANCE", "01")],
    "LUMINANCE_NORMAL": [("LUMINANCE", "00")],

    "MEMORY_1": [("POPMEM", "02 01")],
    "MEMORY_2": [("POPMEM", "02 02")],
    "MEMORY_3": [("POPMEM", "02 03")],
    "MEMORY_4": [("POPMEM", "02 04")],
    "MEMORY_5": [("POPMEM", "02 05")],
    "MEMORY_6": [("POPMEM", "02 06")],
    "MEMORY_7": [("POPMEM", "02 07")],
    "MEMORY_8": [("POPMEM", "02 08")],
    "MEMORY_9": [("POPMEM", "02 09")],
    "MEMORY_10": [("POPMEM", "02 0A")],

    "LENS_MEMORY_1": [("POPLP", "01")],
    "LENS_MEMORY_2": [("POPLP", "02")],
    "LENS_MEMORY_3": [("POPLP", "03")],
    "LENS_MEMORY_4": [("POPLP", "04")],
    "LENS_MEMORY_5": [("POPLP", "05")],
    "LENS_MEMORY_6": [("POPLP", "06")],
    "LENS_MEMORY_7": [("POPLP", "07")],
    "LENS_MEMORY_8": [("POPLP", "08")],
    "LENS_MEMORY_9": [("POPLP", "09")],
    "LENS_MEMORY_10": [("POPLP", "0A")],
    
    "COLOR_SPACE_AUTO" : [('CLRSPACE', '00')],
    "COLOR_SPACE_BT709" : [('CLRSPACE', '01')],
    "COLOR_SPACE_BT2020" : [('CLRSPACE', '02')],

    "HDR_DYNAMIC_RANGE_AUTO":  [('DYNRANGE', '00')],
    "HDR_DYNAMIC_RANGE_SDR":   [('DYNRANGE', '01')],
    "HDR_DYNAMIC_RANGE_HDR10": [('DYNRANGE', '21')],
    "HDR_DYNAMIC_RANGE_HLG":   [('DYNRANGE', '30')],

    "ASPECT_AUTO": [('ASPECT', '30')],
    "ASPECT_FULL": [('ASPECT', '40')],
    "ASPECT_ZOOM": [('ASPECT', '50')],
    "ASPECT_ANAMORPHIC": [('ASPECT', '80')],
    "ASPECT_HORIZ_SQUEEZE": [('ASPECT', '90')],

    "FOCUS_INC": [('FOCUS', 'INC')],
    "FOCUS_DEC": [('FOCUS', 'DEC')],
}

EPSON_CONFIG_RANGES = {
    'HDR_RANGE': {
        'epson_code': 'HDRPQ', 
        'valid_range': range(1, 17),
        'value_translator': None,
        'human_name': 'HDR Range',
        'humanized_range': range(1, 17),
    },
    'SCENE_ADAPTIVE_GAMMA': {
        'epson_code': 'SCENEGAMMA',
        'valid_range': range(0, 256),
        'value_translator': '21',
        'human_name': 'Scene Adaptive Gamma',
        'humanized_range': range(0, 21),
    },
    'HIGH_RESOLUTION_FINE_LINE_ADJUSTMENT': {
        'epson_code': 'SHRF',
        'valid_range': range(0, 256),
        'value_translator': '21',
        'human_name': 'High Resolution Fine Line Adjustment',
        'humanized_range': range(0, 21),
    },
    'HIGH_RESOLUTION_SOFT_FOCUS_DETAIL': {
        'epson_code': 'SHRS',
        'valid_range': range(0, 256),
        'value_translator': '21',
        'human_name': 'High Resolution Soft Focus Detail',
        'humanized_range': range(0, 21),
    },
    'LASER_LEVEL': {
        'epson_code': 'LUMLEVEL',
        'valid_range': range(0,251),
        'value_translator': '50-100',
        'human_name': 'Laser Level',
        'humanized_range': range(50,101),
    },
    'BRIGHTNESS': {
        'epson_code': 'BRIGHT',
        'valid_range': range(0,256),
        'value_translator': '100',
        'human_name': 'Brightness',
        'humanized_range': range(0,101),
    },
    'CONTRAST': {
        'epson_code': 'CONTRAST',
        'valid_range': range(0,256),
        'value_translator': '100',
        'human_name': 'Contrast',
        'humanized_range': range(0,101),
    },
    'DENSITY': {
        'epson_code': 'DENSITY',
        'valid_range': range(0,256),
        'value_translator': '100',
        'human_name': 'Saturation',
        'humanized_range': range(0,101),
    },
    'TINT': {
        'epson_code': 'TINT',
        'valid_range': range(0,256),
        'value_translator': '100',
        'human_name': 'Tint', 
        'humanized_range': range(0,101),
    },
}

EPSON_READOUTS = {
    'FOCUS': {
        'epson_code': 'FOCUS',
        'valid_range': range(0,1024),
        'value_translator': None,
        'human_name': 'Lens Focus',
        'humanized_range': range(0,1024),
    },
    'ZOOM': {
        'epson_code': 'ZOOM',
        'valid_range': range(0,1024),
        'value_translator': None,
        'human_name': 'Lens Zoom',
        'humanized_range': range(0,1024),
    },
    'LENS': {
        'epson_code': 'LENS',
        'valid_range': range(0,1024),
        'value_translator': None,
        'human_name': 'Lens Vertical Shift',
        'humanized_range': range(0,1024),
    },
    'HLENS': {
        'epson_code': 'HLENS',
        'valid_range': range(0,1024),
        'value_translator': None,
        'human_name': 'Lens Horizontal Shift',
        'humanized_range': range(0,1024),
    }
}

EPSON_OPTIONS = {
    'IMGPROC': {
        'human_name': 'Image Processing',
        'epson_command': 'IMGPROC',
        'options': [
            ("Fine", "IMGPROC_FINE", '01'),
            ("Fast", "IMGPROC_FAST", '02')
        ]
    },
    'COLOR_SPACE': {
        'human_name': 'Color Space',
        'epson_command': 'CLRSPACE',
        'options': [
            ("Auto", "COLOR_SPACE_AUTO", '00'),
            ("BT.709", "COLOR_SPACE_BT709", '01'),
            ("BT.2020", "COLOR_SPACE_BT2020", '02'),
        ]
    },
    'HDR_DYNAMIC_RANGE': {
        'human_name': 'HDR Dynamic Range',
        'epson_command': 'DYNRANGE',
        'options': [
            ("Auto", "HDR_DYNAMIC_RANGE_AUTO", '00'),
            ("SDR", "HDR_DYNAMIC_RANGE_SDR", '01'),
            ("HDR10", "HDR_DYNAMIC_RANGE_HDR10", '21'),
            ("HLG", "HDR_DYNAMIC_RANGE_HLG", '30'),
        ]
    },
    'CMODE': {
        'human_name': 'Color Mode',
        'epson_command': 'CMODE',
        'options': [
            ("Dynamic", "CMODE_DYNAMIC", '06'),
            ("Vivid", "CMODE_VIVID", '23'),
            ("Bright Cinema", "CMODE_BRIGHT", '0C'),
            ("Cinema", "CMODE_CINEMA", '15'),
            ("Natural", "CMODE_NATURAL", '07'),            
            ("B&W Cinema", "CMODE_BWCINEMA", '20'),
        ]
    },
    'ASPECT': {
        'human_name': 'Aspect Ratio',
        'epson_command': 'ASPECT',
        'options': [
            ("Auto", "ASPECT_AUTO", '00 30'),
            ("Full", "ASPECT_FULL", '40'),
            ("Zoom", "ASPECT_ZOOM", '50'),
            ("Anamorphic", "ASPECT_ANAMORPHIC", '80'),
            ("Horizontal Squeeze", "ASPECT_HORIZ_SQUEEZE", '90'),
        ]
    },
}


DEFAULT_TIMEOUT_TIME = 1
TIMEOUT_TIMES = {"PWR ON": 40, "PWR OFF": 10, "SOURCE": 5, "ALL": 1}

DEFAULT_SOURCES = {
    "HDMI1": "HDMI1",
    "HDMI2": "HDMI2",
    "PC": "PC",
    "VIDEO": "VIDEO",
    "USB": "USB",
    "LAN": "LAN",
    "WFD": "WiFi Direct",
}

SOURCE_LIST = {
    "30": "HDMI1",
    "10": "PC",
    "40": "VIDEO",
    "52": "USB",
    "53": "LAN",
    "56": "WDF",
    "A0": "HDMI2",
    "41": "VIDEO",
}

INV_SOURCES = {v: k for k, v in DEFAULT_SOURCES.items()}

CMODE_LIST = {
    "00": "Auto",
    "15": "Cinema",
    "07": "Natural",
    "0C": "Bright Cinema",
    "06": "Dynamic",
    "17": "3D Cinema",
    "18": "3D Dynamic",
    "19": "3D THX",
    "20": "B&W Cinema",
    "21": "Adobe RGB",
    "22": "Digital Cinema",
    "23": "Vivid",
    "13": "THX",
    "0D": "Game",
    "16": "Stage",
    "C1": "AutoColor",
    "0B": "x.v. color",
    "05": "Theatre",
    "09": "Theatre Black 1/HD",
    "0A": "Theatre Black 2/Silver Screen",
}

CMODE_LIST_SET = {
    "cinema": "CMODE_CINEMA",
    "Cinema": "CMODE_CINEMA",
    "natural": "CMODE_NATURAL",
    "Natural": "CMODE_NATURAL",
    "bright cinema": "CMODE_BRIGHT",
    "Bright Cinema": "CMODE_BRIGHT",
    "dynamic": "CMODE_DYNAMIC",
    "Dynamic": "CMODE_DYNAMIC",
    "3ddynamic": "CMODE_3DDYNAMIC",
    "3D Dynamic": "CMODE_3DDYNAMIC",
    "3dcinema": "CMODE_3DCINEMA",
    "3D Cinema": "CMODE_3DCINEMA",
    "auto": "CMODE_AUTO",
    "Auto": "CMODE_AUTO",
    "3dthx": "CMODE_3DTHX",
    "3D THX": "CMODE_3DTHX",
    "bwcinema": "CMODE_BWCINEMA",
    "B&W Cinema": "CMODE_BWCINEMA",
    "adobe rgb": "CMODE_ARGB",
    "Adobe RGB": "CMODE_ARGB",
    "digital cinema": "CMODE_DCINEMA",
    "Digital Cinema": "CMODE_DCINEMA",
    "thx": "CMODE_THX",
    "THX": "CMODE_THX",
    "game": "CMODE_GAME",
    "Game": "CMODE_GAME",
    "stage": "CMODE_STAGE",
    "Stage": "CMODE_STAGE",
    "autocolor": "CMODE_AUTOCOLOR",
    "AutoColor": "CMODE_AUTOCOLOR",
    "xv": "CMODE_XV",
    "x.v. color": "CMODE_XV",
    "theatre": "CMODE_THEATRE",
    "Theatre": "CMODE_THEATRE",
    "theatre black": "CMODE_THEATREBLACK",
    "theatre black 2": "CMODE_THEATREBLACK2",
    "Vivid": "CMODE_VIVID",
}


STATE_UNAVAILABLE = "unavailable"
