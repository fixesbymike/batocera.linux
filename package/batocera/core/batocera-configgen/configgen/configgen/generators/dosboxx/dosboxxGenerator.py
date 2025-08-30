from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Final

from ... import Command
from ...batoceraPaths import CONFIGS
from ...utils.configparser import CaseSensitiveConfigParser
from ..Generator import Generator

if TYPE_CHECKING:
    from ...types import HotkeysContext

_CONFIG_DIR: Final = CONFIGS / 'dosbox'
_CONFIG: Final = _CONFIG_DIR / 'dosboxx.conf'

class DosBoxxGenerator(Generator):

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        # Find rom path
        gameConfFile = rom / "dosbox.cfg"

        configFile = _CONFIG
        if gameConfFile.is_file():
            configFile = gameConfFile

        # configuration file
        iniSettings = CaseSensitiveConfigParser(interpolation=None)

        # copy config file to custom config file to avoid overwritting by dosbox-x
        customConfFile = _CONFIG_DIR / 'dosboxx-custom.conf'

        if configFile.exists():
            shutil.copy2(configFile, customConfFile)
            iniSettings.read(customConfFile)

        # sections
        if not iniSettings.has_section("sdl"):
            iniSettings.add_section("sdl")
        iniSettings.set("sdl", "output", "opengl")

        # save
        with customConfFile.open('w') as config:
            iniSettings.write(config)

        # -fullscreen removed as it crashes on N2
        commandArray = ['/usr/bin/dosbox-x',
                        "-exit"]

        # Mounting decisions:
        # 1. If the directory contains a .img file, we guess that it is a bootable dosbox hdd img file. We mount it as c: and we'll boot from there.
        # 2. Otherwise, we mount the directory as c: drive and run dosbox.bat
        # 3. If the directory contains a .iso file, we mount it as d: drive
        mountDDrive = []
        for file in rom.iterdir():
            if file.suffix in [".iso", ".cue", ".mdf", ".chd"]:
                mountDDrive = ["-c", f"""imgmount d {file!s}"""]
        commandArray.extend(mountDDrive)

        mountCDrive = ["-c", f"""mount c {rom!s}""",
                       "-c", "c:",
                       "-c", "dosbox.bat"]
        for file in rom.iterdir():
            if file.suffix in [".img", ".qcow2", ".vhd", ".nhd", ".hdi"]:
                mountCDrive = ["-c", f"""imgmount c {file!s}""",
                               "-c", "boot c:"]
        commandArray.extend(mountCDrive)

        # Other options
        commandArray.extend(["-fastbioslogo",
                             "-conf", f"{customConfFile!s}"]

        return Command.Command(array=commandArray, env={"XDG_CONFIG_HOME":CONFIGS})

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "dosboxx",
            "keys": { "exit": ["KEY_LEFTCTRL", "KEY_F9"] }
        }
