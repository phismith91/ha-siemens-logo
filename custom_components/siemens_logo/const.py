DOMAIN = "siemens_logo"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_POINTS = "points"
CONF_POINTS_SOURCE = "points_source"
CONF_FILE_PATH = "file_path"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 10

PLATFORMS = ["sensor", "switch", "binary_sensor"]

POINTS_SOURCE_MANUAL = "manual"
POINTS_SOURCE_FILE = "file"
POINTS_SOURCE_LOGO8_DEFAULT = "logo8_default"

# Standard Modbus-Adressen für LOGO! 8 (0BA8), Firmware FS4+
# I1-I8: Discrete Inputs 1-8
# Q1-Q8: Coils 8192-8199 (0x2000)
# AI1-AI8: Holding Registers 0-7
# AQ1-AQ2: Holding Registers 528-529
# M1-M8: Coils 8256-8263 (0x2040)
LOGO8_DEFAULT_POINTS: list[dict] = [
    {"key": "i1", "name": "LOGO I1", "platform": "binary_sensor", "kind": "discrete", "address": 1},
    {"key": "i2", "name": "LOGO I2", "platform": "binary_sensor", "kind": "discrete", "address": 2},
    {"key": "i3", "name": "LOGO I3", "platform": "binary_sensor", "kind": "discrete", "address": 3},
    {"key": "i4", "name": "LOGO I4", "platform": "binary_sensor", "kind": "discrete", "address": 4},
    {"key": "i5", "name": "LOGO I5", "platform": "binary_sensor", "kind": "discrete", "address": 5},
    {"key": "i6", "name": "LOGO I6", "platform": "binary_sensor", "kind": "discrete", "address": 6},
    {"key": "i7", "name": "LOGO I7", "platform": "binary_sensor", "kind": "discrete", "address": 7},
    {"key": "i8", "name": "LOGO I8", "platform": "binary_sensor", "kind": "discrete", "address": 8},
    {"key": "q1", "name": "LOGO Q1", "platform": "switch", "kind": "coil", "address": 8192},
    {"key": "q2", "name": "LOGO Q2", "platform": "switch", "kind": "coil", "address": 8193},
    {"key": "q3", "name": "LOGO Q3", "platform": "switch", "kind": "coil", "address": 8194},
    {"key": "q4", "name": "LOGO Q4", "platform": "switch", "kind": "coil", "address": 8195},
    {"key": "q5", "name": "LOGO Q5", "platform": "switch", "kind": "coil", "address": 8196},
    {"key": "q6", "name": "LOGO Q6", "platform": "switch", "kind": "coil", "address": 8197},
    {"key": "q7", "name": "LOGO Q7", "platform": "switch", "kind": "coil", "address": 8198},
    {"key": "q8", "name": "LOGO Q8", "platform": "switch", "kind": "coil", "address": 8199},
    {"key": "ai1", "name": "LOGO AI1", "platform": "sensor", "kind": "holding", "address": 0},
    {"key": "ai2", "name": "LOGO AI2", "platform": "sensor", "kind": "holding", "address": 1},
    {"key": "ai3", "name": "LOGO AI3", "platform": "sensor", "kind": "holding", "address": 2},
    {"key": "ai4", "name": "LOGO AI4", "platform": "sensor", "kind": "holding", "address": 3},
    {"key": "ai5", "name": "LOGO AI5", "platform": "sensor", "kind": "holding", "address": 4},
    {"key": "ai6", "name": "LOGO AI6", "platform": "sensor", "kind": "holding", "address": 5},
    {"key": "ai7", "name": "LOGO AI7", "platform": "sensor", "kind": "holding", "address": 6},
    {"key": "ai8", "name": "LOGO AI8", "platform": "sensor", "kind": "holding", "address": 7},
    {"key": "aq1", "name": "LOGO AQ1", "platform": "sensor", "kind": "holding", "address": 528},
    {"key": "aq2", "name": "LOGO AQ2", "platform": "sensor", "kind": "holding", "address": 529},
    {"key": "m1", "name": "LOGO M1", "platform": "binary_sensor", "kind": "coil", "address": 8256},
    {"key": "m2", "name": "LOGO M2", "platform": "binary_sensor", "kind": "coil", "address": 8257},
    {"key": "m3", "name": "LOGO M3", "platform": "binary_sensor", "kind": "coil", "address": 8258},
    {"key": "m4", "name": "LOGO M4", "platform": "binary_sensor", "kind": "coil", "address": 8259},
    {"key": "m5", "name": "LOGO M5", "platform": "binary_sensor", "kind": "coil", "address": 8260},
    {"key": "m6", "name": "LOGO M6", "platform": "binary_sensor", "kind": "coil", "address": 8261},
    {"key": "m7", "name": "LOGO M7", "platform": "binary_sensor", "kind": "coil", "address": 8262},
    {"key": "m8", "name": "LOGO M8", "platform": "binary_sensor", "kind": "coil", "address": 8263},
]
