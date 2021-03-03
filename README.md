# Wintertools

*Wintertools* is a set of Python utilities used by [Winterbloom](https://winterbloom.com) projects.

## What's in here?

**This is an incomplete list!**

Tools for firmware development:

* [`wintertools.buildgen`](wintertools/buildgen.py) is a flexible set of utilities for writing `configure.py` scripts for building with [Ninja](https://ninja-build.org/). Here's an [example](https://github.com/theacodes/Winterbloom_Castor_and_Pollux/blob/main/firmware/configure.py).
* [`wintertools.build_info`](wintertools/build_info.py) generates a C file containing information about the firmware's build context - git commit, date, compiler version, etc.
* [`wintertools.fw_size`](wintertools/fw_size.py) analyzes the flash and RAM usage of a firmware build.

Tools for building hardware program & test scripts:

* [`wintertools.circuitpython`](wintertools/circuitpython.py) provides basic interaction with devices running CircuitPython.
* [`wintertools.fw_fetch`](wintertools/fw_fetch.py) can fetch the latest `uf2-samdx1` bootloader and CircuitPython for a given board.
* [`wintertools.jlink`](wintertools/jlink.py) provides a simple high-level way of invoking the [J-Link Commander](https://wiki.segger.com/J-Link_Commander).
* [`wintertools.keyboard`](wintertools/keyboard.py) provides a means for listening to key input in terminal-based programs, useful for factory setup scripts that allow adjusting some value using the arrow keys.
* [`wintertools.multimeter`](wintertools/multimeter.py) provides an interface to the [Keithley DMM6500](https://www.tek.com/tektronix-and-keithley-digital-multimeter/dmm6500) precision multimeter.
* [`wintertools.oscilloscope`](wintertools/oscilloscope.py) provides an interface to the [Siglent SDS1104X-E](https://siglentna.com/product/sds1104x-e-100-mhz/) oscilloscope.
* [`wintertools.sol`](wintertools/sol.py) provides a means of controlling Sol via scripts to produce accurate voltage references during testing and calibration.

Other tools:

* [`wintertools.fs`](wintertools/fs.py) provides helpers for interacting with the filesystem, including finding external drives by name and copying over complex sets of files.
* [`wintertools.git`](wintertools/git.py) gives some basic interaction with `git`.
* [`wintertools.midi`](wintertools/midi.py) provides a high-level `MIDIDevice` class for interacting with Winterbloom's devices over MIDI SysEx.
* [`wintertools.teeth`](wintertools/teeth.py) implements an 8-bit to 7-bit binary encoding scheme.
* [`wintertools.tui`](wintertools/tui.py) provides helpers for creating terminal-based programs.


## Contributing

While I don't really expect anyone outside of Winterbloom to use these, by all means, contributions are welcome. File an issue or reach out to us before you write code, so we can make sure it's something that'll be beneficial for all of us. :)

## License

Wintertools is published under the [MIT License](LICENSE)
