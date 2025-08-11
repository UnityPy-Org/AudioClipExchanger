import os
from typing import cast, get_args

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:
    from wheel.bdist_wheel import bdist_wheel  # type: ignore


BDIST_TAG_FMOD_MAP = {
    # Windows
    "win32": "x86",
    "win_amd64": "x64",
    "win_arm64": "arm",
    # Linux and Mac endings
    "arm64": "arm64",  # Mac
    "x86_64": "x64",
    "aarch64": "arm64",  # Linux
    "i686": "x86",
    "armv7l": "arm",  # armhf
}


class SDist(sdist):
    def make_distribution(self) -> None:
        # add all fmod libraries to the distribution
        self.filelist.files.extend(
            [
                f"{root}/{file}".replace("\\", "/")
                for root, _, files in os.walk("fmod_toolkit/libfmod")
                for file in files
                if file.endswith((".dll", ".so", ".dylib"))
            ]
        )
        return super().make_distribution()


class BDistWheel(bdist_wheel):  # type: ignore
    def finalize_options(self, *args, **kwargs):
        super().finalize_options(*args, **kwargs)

    def run(self):
        # Determine platform-specific binary for this wheel
        platform_tag = self.get_tag()[2]
        if platform_tag.startswith("win"):
            system = "Windows"
            arch = BDIST_TAG_FMOD_MAP[platform_tag]
        else:
            arch = next(
                (v for k, v in BDIST_TAG_FMOD_MAP.items() if platform_tag.endswith(k)),
                None,
            )
            system = "Darwin" if platform_tag.startswith("macosx") else "Linux"

        # import here to avoid root level import issues related to not finding fmod_toolkit
        from fmod_toolkit.importer import ARCHS, get_fmod_path_for_config

        if arch in get_args(ARCHS):
            fmod_path = get_fmod_path_for_config(system, cast(ARCHS, arch))
            self.distribution.package_data["fmod_toolkit"].append(fmod_path)

        super().run()

    def get_tag(self):
        self.root_is_pure = False
        impl, abi_tag, plat_name = super().get_tag()
        if impl.startswith("cp"):
            # hard set 3.8 for CPython
            # TODO: handle other python interpreters
            return "cp38", "abi3", plat_name
        self.root_is_pure = True
        return impl, abi_tag, plat_name


setup(
    name="fmod_toolkit",
    packages=find_packages(),
    package_data={"fmod_toolkit": []},
    cmdclass={"sdist": SDist, "bdist_wheel": BDistWheel},
)
