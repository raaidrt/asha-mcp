"""
Hatchling custom build hook for downloading Stockfish binaries
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class StockfishBuildHook(BuildHookInterface):
    """Custom build hook to download and include Stockfish binaries."""

    PLUGIN_NAME = 'stockfish'

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize the build hook."""
        self.version = version
        self.build_data = build_data

        # Get configuration from pyproject.toml
        self.target_dir = self.config.get('target_dir', 'stockfish_binaries')
        self.force_download = self.config.get('force_download', False)

        # Create target directory
        self.target_path = Path(self.root) / self.target_dir
        self.target_path.mkdir(exist_ok=True)

    def clean(self, versions: list[str]) -> None:
        pass

    def finalize(
        self, version: str, build_data: Dict[str, Any], artifact_path: str
    ) -> None:
        """Download Stockfish binaries after build setup."""
        try:
            self._download_stockfish_binary()
            binary = self._verify_binary_exists()
            print(f'Stockfish binary created at {binary}')
        except Exception as e:
            print(f'Failed to download Stockfish binary: {e}')
            raise e

    def _download_stockfish_binary(self) -> None:
        """Download and extract Stockfish binary using the shell script."""
        # Check if stockfish binary already exists
        existing_files = list(self.target_path.iterdir())
        if existing_files and not self.force_download:
            if len(existing_files) == 1 and existing_files[0].is_file():
                stockfish_binary = existing_files[0]
                print(f'Stockfish binary already exists at {stockfish_binary}')
                return
            else:
                raise RuntimeError(
                    f'Unexpected files in {self.target_path}: {existing_files}'
                )

        # Check if download_stockfish.sh script exists
        script_path = Path(self.root) / 'src/asha/download_stockfish.sh'
        if not script_path.exists():
            raise FileNotFoundError(f'Download script not found at {script_path}')

        # Make script executable
        script_path.chmod(script_path.stat().st_mode | 0o755)

        # Run the download script
        print(f'Running download script: {script_path}')
        try:
            result = subprocess.run(
                [str(script_path), '--directory', str(self.target_dir)],
                stdout=None,  # Use parent's stdout
                stderr=None,  # Use parent's stderr
                text=True,
                cwd=self.root,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f'Download script failed with return code {result.returncode}'
                )

            print(f'Successfully downloaded Stockfish to {self.target_path}')

        except subprocess.TimeoutExpired:
            raise RuntimeError('Download script timed out after 5 minutes')
        except Exception as e:
            raise RuntimeError(f'Failed to run download script: {e}')

    def _verify_binary_exists(self) -> Path:
        """Verify the downloaded binary exists."""
        if not self.target_path.exists():
            raise FileNotFoundError(f'Stockfish binary not found at {self.target_path}')
        files = list(self.target_path.iterdir())
        if len(files) != 1:
            raise RuntimeError(
                f'Expected exactly one file in {self.target_path}, found: {files}'
            )
        if not files[0].is_file():
            raise RuntimeError(f'Expected file but found directory: {files[0]}')
        return files[0]
