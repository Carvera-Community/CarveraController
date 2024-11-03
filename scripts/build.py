#!/usr/bin/python3
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__
import pyinstaller_versionfile
from setuptools_scm import get_version

from . import patch_pyinstaller

logger = logging.getLogger(__name__)

# ------ Build config ------
APP_NAME = "CarveraController-Community"
PACKAGE_NAME = "carveracontroller"
ASSETS_FOLDER = "packaging_assets"

# ------ Versionfile info ------
COMPANY_NAME = "Carvera-Community"
FILE_DESCRIPTION = APP_NAME
INTERNAL_NAME = APP_NAME
LEGAL_COPYRIGHT = "GNU General Public License v2.0"
PRODUCT_NAME = APP_NAME


# ------ Build paths ------
BUILD_PATH = Path(__file__).parent.resolve()
ROOT_PATH = BUILD_PATH.parent.resolve()
PROJECT_PATH = BUILD_PATH.parent.joinpath(PACKAGE_NAME).resolve()
PACKAGE_PATH = PROJECT_PATH.resolve()
ROOT_ASSETS_PATH = ROOT_PATH.joinpath(ASSETS_FOLDER).resolve()


def build_pyinstaller_args(
    os: str,
    output_filename: str,
    versionfile_path: Path | None = None,
) -> list[str]:
    logger.info("Build Pyinstaller args.")
    build_args = []
    script_entrypoint = f"carveracontroller/main.py"

    logger.info(f"entrypoint: {script_entrypoint}")
    build_args += [script_entrypoint]

    logger.info(f"Path to search for imports: {PACKAGE_PATH}")
    build_args += ["-p", f"{PACKAGE_PATH}"]

    logger.info(f"Spec file path: {BUILD_PATH}")
    build_args += ["--specpath", f"{BUILD_PATH}"]

    logger.info(f"Output exe filename: {output_filename}")
    build_args += ["-n", output_filename]

    if os == "macos":
        logger.info(f"Output file icon: {ROOT_ASSETS_PATH.joinpath('icon-src.icns')}")
        build_args += ["--icon", f"{ROOT_ASSETS_PATH.joinpath('icon-src.icns')}"]
    if os == "windows":
        logger.info(f"Output file icon: {ROOT_ASSETS_PATH.joinpath('icon-src.ico')}")
        build_args += ["--icon", f"{ROOT_ASSETS_PATH.joinpath('icon-src.ico')}"]
    else:
        logger.info(f"Output file icon: {ROOT_ASSETS_PATH.joinpath('icon-src.png')}")
        build_args += ["--icon", f"{ROOT_ASSETS_PATH.joinpath('icon-src.png')}"]

    logger.info(f"Add bundled package assets: {PACKAGE_PATH}")
    build_args += ["--add-data", f"{PACKAGE_PATH}:."]

    logger.info("Build options: noconsole, noconfirm, noupx, clean")
    build_args += [
        "--noconsole",
        "--onefile",
        # "--debug=all",  # debug output toggle
        "--noconfirm",
        "--noupx",  # Not sure if the false positive AV hits are worth it
        "--clean",
    ]

    if versionfile_path is not None:
        logger.info(f"Versionfile path: {versionfile_path}")
        build_args += ["--version-file", f"{versionfile_path}"]

    print(" ".join(build_args))
    return build_args


def run_pyinstaller(build_args: list[str]) -> None:
    PyInstaller.__main__.run(build_args)

def get_version_info() -> str:
    version_str = get_version(root='..', relative_to=__file__)
    logger.info(f"Version determined to be {version_str}")
    return version_str

def generate_versionfile(package_version: str, output_filename: str) -> Path:
    logger.info("Generate versionfile.txt.")
    versionfile_path = BUILD_PATH.joinpath("versionfile.txt")
    pyinstaller_versionfile.create_versionfile(
        output_file=versionfile_path,
        version=package_version,
        company_name=COMPANY_NAME,
        file_description=FILE_DESCRIPTION,
        internal_name=INTERNAL_NAME,
        legal_copyright=LEGAL_COPYRIGHT,
        original_filename=f"{output_filename}.exe",
        product_name=PRODUCT_NAME,
    )

    return versionfile_path

def run_appimage_builder()-> None:
    command = "appimage-builder --recipe packaging_assets/AppImageBuilder.yml"
    result = subprocess.run(command, shell=True, capture_output=False, text=True)
    if result.returncode != 0:
        logger.error(f"Error executing command: {command}")
        logger.error(f"stderr: {result.stderr}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--os",
        metavar="os",
        required=True,
        choices=["windows", "macos", "linux"],
        type=str,
        default="linux",
        help="Choices are: windows, macos, or linux. Default is linux."
    )

    # temp workaround for https://github.com/kivy/kivy/issues/8653
    patch_pyinstaller.main()

    args = parser.parse_args()
    os = args.os
    package_version = get_version_info()
    output_filename = PACKAGE_NAME
    versionfile_path = None

    if os == "windows":
        versionfile_path = generate_versionfile(
            package_version=package_version,
            output_filename=output_filename,
        )

    build_args = build_pyinstaller_args(
        os=os,
        output_filename=output_filename,
        versionfile_path=versionfile_path,
    )
    run_pyinstaller(build_args=build_args)

    if os == "linux":
        run_appimage_builder()

if __name__ == "__main__":
    main()
