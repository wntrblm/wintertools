# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Helpers for generating ninja builds
"""

import os
import pathlib
import shutil
import subprocess
import sys

GCC = "arm-none-eabi-gcc"
OBJCOPY = "arm-none-eabi-objcopy"
_GCC_INSTALL_URL = "https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads"


# Environment helpers


def check_python_version(min_version="3.9.0"):
    min_version_tuple = tuple(int(x) for x in min_version.split("."))
    if sys.version_info < min_version_tuple:
        print(
            f"Requires python >= {min_version}. install from https://www.python.org/downloads/"
        )
        sys.exit(1)


def check_gcc_version(min_version="10.2.0"):
    if not shutil.which(GCC):
        print(f"Requires {GCC}, install from {_GCC_INSTALL_URL}")
        sys.exit(1)

    gcc_version = (
        subprocess.run(
            ["arm-none-eabi-gcc", "-dumpversion"],
            capture_output=True,
            check=True,
            text=True,
        )
        .stdout.strip()
        .split(".")
    )

    gcc_version_tuple = tuple(int(x) for x in gcc_version)
    min_version_tuple = tuple(int(x) for x in min_version.split("."))

    if gcc_version_tuple < min_version_tuple:
        print(f"Requires {GCC} >= {min_version}, install from {_GCC_INSTALL_URL}")
        sys.exit(1)


def ensure_directory():
    """
    Makes sure that the current working directory is the directory that holds
    the script that's being run.
    """
    os.chdir(pathlib.Path(sys.modules["__main__"].__file__).parent)


# Common flags & defines for MCUs used by Winterbloom


class Desktop:
    """Used for tests"""

    @classmethod
    def common_flags(cls) -> list:
        return [
            "-funsigned-char -fshort-enums",
            # Because of how Ninja runs gcc it doesn't know that it has an interactive
            # terminal and disables color output. This makes sure it always outputs color.
            "-fdiagnostics-color=always",
        ]

    @classmethod
    def cc_flags(cls):
        return [
            # Error on all warnings and enable several useful warnings.
            # -Wall turns on warning for questionable patterns that should be easy to fix.
            # -Wextra adds a few more on top of -Wall that should also be easy to fix.
            # -Wdouble-promotion warns when a value is automatially promoted to a double.
            #   this is especially useful because any code that deals with doubles will
            #   be large and slow and we definitely want to avoid that.
            # -Wformat=2 checks calls to printf & friends to make sure the format specifiers
            #   match the types of the arguments.
            # -Wundef checks for undefined indentifiers in #if macros.
            "-W -Wall -Wextra -Werror -Wformat=2 -Wundef",
            # Other flags that might be useful:
            # -Wconversion warn about implicit integer conversions
        ]

    @classmethod
    def ld_flags(cls):
        return []

    @classmethod
    def defines(cls) -> dict:
        return {}


class CortexM:
    FPU = "auto"

    @classmethod
    def common_flags(cls) -> list:
        return [
            # Configure the specific Cortex-M variant.
            f"-mcpu={cls.CPU}",
            f"-mfloat-abi={cls.FLOAT_ABI}",
            f"-mfpu={cls.FPU}",
            # Select C11 + GNU extensions as the program's C dialect.
            "--std=gnu11",
            # Use newlib-nano, a very minimal libc.
            "--specs=nano.specs",
            # Cortex-M CPUs only support the Thumb instruction set.
            "-mthumb",
            # Tells the compiler to use ARM's EABI with variable-length enums.
            # The alternative is aapcs-linux which is the same with fixed-length
            # 4-byte enums.
            # AAPCS here refers to the ARM Architecture Procedure Call Standard.
            # https://developer.arm.com/documentation/ihi0042/j/?lang=en
            "-mabi=aapcs",
            # Set some C dialect options that are useful for embedded development:
            # - char is always unsigned.
            # - bitfields are always unsigned.
            # - put each enum into the smallest type that'll hold its values.
            "-funsigned-char -funsigned-bitfields -fshort-enums",
            # Enable unused code/data elimination. This flag makes the compiler generate
            # individual sections for each static variable and function instead of
            # combining them together. The linker can cull them during linking.
            # https://interrupt.memfault.com/blog/best-and-worst-gcc-clang-compiler-flags#-ffunction-sections--fdata-sections----gc-sections
            "-fdata-sections -ffunction-sections",
            # Because of how Ninja runs gcc it doesn't know that it has an interactive
            # terminal and disables color output. This makes sure it always outputs color.
            "-fdiagnostics-color=always",
        ]

    @classmethod
    def cc_flags(cls):
        return [
            # Error on all warnings and enable several useful warnings.
            # -Wall turns on warning for questionable patterns that should be easy to fix.
            # -Wextra adds a few more on top of -Wall that should also be easy to fix.
            # -Wshadow warns about a local symbol shadowing a global symbol.
            # -Wdouble-promotion warns when a value is automatially promoted to a double.
            #   this is especially useful because any code that deals with doubles will
            #   be large and slow and we definitely want to avoid that.
            # -Wformat=2 checks calls to printf & friends to make sure the format specifiers
            #   match the types of the arguments.
            # -Wundef checks for undefined indentifiers in #if macros.
            "-W -Wall -Wextra -Werror -Wshadow -Wdouble-promotion -Wformat=2 -Wundef",
            # Other flags that might be useful:
            # -Wconversion warn about implicit integer conversions
        ]

    @classmethod
    def ld_flags(cls):
        return [
            # Remove unused sections. The compiler generates individual sections for
            # each function and immutable data and the linker can determine if they're
            # unused and cull them.
            "-Wl,--gc-sections",
            # Output a link map. This is helpful when debugging.
            "-Wl,-Map=$builddir/link.map",
        ]

    @classmethod
    def defines(cls) -> dict:
        return {}


class SAMD21(CortexM):
    CPU = "cortex-m0plus"
    FLOAT_ABI = "soft"

    @classmethod
    def defines(cls, mcu: str) -> dict:
        defines = super().defines()
        defines.update(
            {
                # Used in CMSIS device support header. See sam.h.
                f"__{mcu}__": 1,
                # Used in some third_party code, like libwinter, to detect SAM D variants.
                "SAMD21": 1,
                # Used in CMSIS math headers.
                # see https://github.com/ARM-software/CMSIS/blob/master/CMSIS/Include/arm_math.h#L84-L88
                "ARM_MATH_CM0PLUS": 1,
            }
        )

        return defines


# Collection helpers


def strigify_paths(paths: list) -> list:
    return [str(path) for path in paths]


def remove_relative_parts(path: pathlib.Path) -> pathlib.Path:
    """Removes any leading ".." in a path."""
    return pathlib.Path(*[part for part in path.parts if part != ".."])


def expand_srcs(srcs: list) -> list:
    """Expands globs in a list of source patterns into a list of Paths"""
    result = []
    for pattern in srcs:
        if any(_ in pattern for _ in ("*", "[", "?")):
            expanded = pathlib.Path(".").glob(pattern)
            if not expanded:
                print(f"No files match {pattern}")
                sys.exit(1)
            result.extend(expanded)
        else:
            result.append(pathlib.Path(".", pattern))
    return result


def includes_from_srcs(srcs) -> list:
    """Generates a list of include directories for the given set of source Paths"""
    return list(set((pathlib.Path(path).parent for path in srcs)))


def format_includes(includes: list) -> str:
    """Format includes into the argument expected by GCC"""
    return " ".join([f"-I{path}" for path in includes])


def format_defines(defines: list) -> str:
    """Format defines into the argument expected by GCC"""
    return " ".join([f"-D{key}={value}" for key, value in defines.items()])


# Global variable helpers


def toolchain_variables(
    writer,
    cc_flags: list,
    linker_flags: list,
    includes: list,
    defines: list,
    builddir: str = "./build",
):
    """Outputs Ninja needed for the GCC-related rules."""
    if isinstance(defines, dict):
        defines = format_defines(defines)

    if isinstance(includes, list):
        includes = format_includes(includes)

    writer.variable("builddir", "./build")
    writer.newline()
    writer.variable(
        "cc_flags",
        " ".join(cc_flags),
    )
    writer.newline()
    writer.variable("cc_includes", includes)
    writer.newline()
    writer.variable("cc_defines", defines)
    writer.newline()
    writer.variable("ld_flags", " ".join(linker_flags))
    writer.newline()


# Rule generators


def cc_rule(writer):
    writer.rule(
        name="cc",
        command=f"{GCC} $cc_flags $cc_includes $cc_defines -MMD -MT $out -MF $out.d -c $in -o $out",
        depfile="$out.d",
        deps="gcc",
        description="Compile $in",
    )
    writer.newline()


def ld_rule(writer):
    writer.rule(
        name="ld",
        command=f"{GCC} $ld_flags $in -o $out",
        description="Link $out",
    )
    writer.newline()


def output_format_rules(writer):
    """Generates rules for creating bin & uf2 files."""
    writer.rule(
        name="elf_to_bin",
        command=f"{OBJCOPY} -O binary $in $out",
        description="Create $out",
    )
    writer.newline()
    writer.rule(
        name="bin_to_uf2",
        command="python3 -m wintertools.bin_to_uf2 $in $out",
        description="Create $out",
    )
    writer.newline()


def runcmd_rules(writer):
    """
    Rules for running various commands without needing to explicitly create
    a separate rule for them.
    """
    writer.newline()
    writer.rule(
        name="runcmd_arg_in", command="$cmd $in $append", description="$desc $in"
    )
    writer.newline()
    writer.rule(
        name="runcmd_arg_in_shh", command="$cmd $in $append", description="$desc"
    )
    writer.newline()
    writer.rule(
        name="runcmd_arg_out", command="$cmd $out $append", description="$desc $out"
    )
    writer.newline()


def structy_rule(writer):
    """Generates a rule for compiling structy definitions into sources."""
    writer.rule(
        name="structy",
        command="python3 -m structy_generator -l $lang $in $dest",
        description="Structy generate ($lang) $in -> $dest",
    )


def clang_format_rule(writer):
    writer.rule(
        name="clang_format",
        command="clang-format -i $in && touch $out",
        description="Format $in",
    )
    writer.newline()


def clang_tidy_rule(writer):
    writer.rule(
        name="clang_tidy",
        command="clang-tidy $srcs $args -- $cc_includes $cc_defines",
        description="Tidy",
    )
    writer.newline()


def common_rules(writer):
    cc_rule(writer)
    ld_rule(writer)
    output_format_rules(writer)
    runcmd_rules(writer)
    structy_rule(writer)
    clang_format_rule(writer)
    clang_tidy_rule(writer)


# Build generators


def object_build(writer, src: pathlib.Path) -> pathlib.Path:
    """Generates a build for turning source file into an object file."""
    object_path = pathlib.Path("$builddir") / remove_relative_parts(
        src.with_suffix(".o")
    )

    writer.build(outputs=str(object_path), rule="cc", inputs=str(src))

    writer.newline()
    return object_path


def compile_build(writer, srcs: list) -> list:
    """Generates object builds for all of the given srcs."""
    return [object_build(writer, src) for src in srcs]


def link_build(writer, program: str, objects: list, ext=".elf"):
    """Generates a build to link the given project with the given objects."""
    writer.build(f"build/{program}{ext}", "ld", strigify_paths(objects))
    writer.newline()


def size_build(writer, program: str, flash_size: int, ram_size: int):
    """Generates a build to run wintertools' size analyzer."""
    writer.build(
        "size.phony",
        "runcmd_arg_in",
        f"$builddir/{program}.elf",
        variables=dict(
            cmd=f"python3 -m wintertools.fw_size --flash-size {flash_size} --ram-size {ram_size}",
            desc="Size",
        ),
    )
    writer.newline()

    writer.build("size", "phony", "size.phony")
    writer.newline()


def binary_formats_build(writer, program: str):
    """Generates builds to output bin & uf2 files."""
    writer.build(
        f"build/{program}.bin",
        "elf_to_bin",
        f"build/{program}.elf",
    )
    writer.newline()

    writer.build(
        f"build/{program}.uf2",
        "bin_to_uf2",
        f"build/{program}.bin",
    )
    writer.newline()


def structy_build(writer, src: str, **langs_to_dests):
    """Generates a build to compile a struct definition."""
    for lang, dest in langs_to_dests.items():
        output_stem = pathlib.Path(src).stem
        outputs = [pathlib.Path(dest, f"{output_stem}.{lang}")]

        # Include the header as well for C.
        if lang == "c":
            outputs.append(pathlib.Path(dest, f"{output_stem}.h"))

        writer.build(
            strigify_paths(outputs),
            "structy",
            src,
            variables=dict(lang=lang, dest=dest),
        )
        writer.newline()


def build_info_build(writer, build_config: str):
    """Generates a build to create build info using wintertools.build_info."""
    writer.build(
        "$builddir/generated_build_info.c",
        "runcmd_arg_out",
        "",
        variables=dict(
            cmd=f"python3 -m wintertools.build_info --config {build_config}",
            desc="Generate build info",
        ),
        implicit=["build_info_always.phony"],
    )
    writer.newline()

    writer.build("build_info_always.phony", "phony")
    writer.newline()


def py_generated_file_build(
    writer, script: str, output: str, desc: str = None, implicit_deps: list = None
):
    """Creates a build that uses a python script to generate a file."""
    if desc is None:
        desc = f"Generate {output}"

    if implicit_deps is None:
        implicit_deps = []

    writer.build(
        output,
        "runcmd_arg_out",
        "",
        variables=dict(
            cmd=f"python3 {script}",
            desc=desc,
        ),
        implicit=[script] + implicit_deps,
    )
    writer.newline()


def clang_format_build(writer, files: list):
    for path in files:
        writer.build(f"$builddir/format/{path}", "clang_format", str(path))
        writer.newline()

    writer.build(
        "format", "phony", implicit=[f"$builddir/format/{path}" for path in files]
    )


def clang_tidy_build(writer, srcs: list):
    writer.build(
        "tidy",
        "clang_tidy",
        variables=dict(
            srcs=strigify_paths(srcs),
            args="-checks=-clang-diagnostic-format",
        ),
    )
    writer.newline()


def reconfigure_build(writer):
    """Generates a special build to re-generated the Ninja file."""
    writer.variable("configure_args", " ".join(sys.argv[1:]))
    writer.newline()
    writer.rule(
        "configure",
        command=f"{sys.executable} {sys.argv[0]} $configure_args",
        generator=True,
        description=f"Reconfigure with {sys.argv[0]} $configure_args",
    )
    writer.newline()
    writer.build("build.ninja", "configure", implicit=[sys.argv[0]])

    writer.close()
