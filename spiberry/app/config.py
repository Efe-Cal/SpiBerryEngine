import configparser
from pathlib import Path
import logging
import argparse
import sys

logger = logging.getLogger("SpiBerryEngine")

CONFIG_PATH = Path.home() / "spiberry_config.ini"
logger.info("Using config file at %s", CONFIG_PATH)

def create_default_config():
    if not CONFIG_PATH.exists():
        config = configparser.ConfigParser()
        config["GPIO"] = {
            "red": "0",
            "green": "11",
            "blue": "9",
            "button": "17",
            "starter": "21",
            "active_high": "False"
        }
        config["Code"] = {
            "path": "~/spiberry/robot_code.py",
            "raspi_functions_path": "~/spiberry/raspi_functions/",
        }
        config["Vision"] = {
            "enabled": "False",
        }
        config["Camera"] = {
            "take_picture_method": "picamera2",
            "timeout": "0",
            "width": "1920",
            "height": "1080",
        }
        config["RemoteDrive"] = {
            "left_motor":"port.A",
            "right_motor":"port.B",
        }

        with open(CONFIG_PATH, "w") as f:
            config.write(f)


def _parse_pin_overrides(argv):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--red", type=int)
    parser.add_argument("--green", type=int)
    parser.add_argument("--blue", type=int)
    parser.add_argument("--button", type=int)

    try:
        parsed_args, _ = parser.parse_known_args(argv)
    except SystemExit:
        logger.warning("Ignoring invalid pin CLI arguments.")
        return {}

    overrides = {}
    for config_key in ["red", "green", "blue", "button"]:
        pin_value = getattr(parsed_args, config_key)
        if pin_value is None:
            continue

        overrides[config_key] = str(pin_value)

    return overrides


def _apply_pin_overrides_from_cli(config_obj: configparser.ConfigParser, config_path: Path):
    pin_overrides = _parse_pin_overrides(sys.argv[1:])
    if not pin_overrides:
        return

    if not config_obj.has_section("GPIO"):
        config_obj["GPIO"] = {}

    for key, value in pin_overrides.items():
        config_obj["GPIO"][key] = value
    try:
        with open(config_path, "w") as f:
            config_obj.write(f)
        logger.info("Applied GPIO pin overrides from CLI args: %s", ", ".join(f"{k}={v}" for k, v in pin_overrides.items()))
    except OSError as e:
        logger.error("Failed to persist GPIO pin overrides to config file: %s", e)

def _resolve_raspi_module_file(configured_path: Path) -> Path:
    if configured_path.suffix == ".py":
        return configured_path
    return configured_path / "__init__.py"


config = configparser.ConfigParser()
config.read(CONFIG_PATH)
_apply_pin_overrides_from_cli(config, CONFIG_PATH)

ROBOT_CODE_PATH = Path(
    config.get("Code", "path", fallback="~/spiberry/robot_code.py")
).expanduser()
if not ROBOT_CODE_PATH.is_absolute():
    ROBOT_CODE_PATH = (Path.home() / "spiberry" / ROBOT_CODE_PATH).resolve()
ROBOT_CODE = str(ROBOT_CODE_PATH)

RASPI_FUNCTIONS_PATH = Path(
    config.get("Code", "raspi_functions_path", fallback="~/spiberry/raspi_functions/")
).expanduser()
if not RASPI_FUNCTIONS_PATH.is_absolute():
    RASPI_FUNCTIONS_PATH = (Path.home() / "spiberry" / RASPI_FUNCTIONS_PATH).resolve()


RASPI_FUNCTIONS_MODULE_FILE = _resolve_raspi_module_file(RASPI_FUNCTIONS_PATH)
