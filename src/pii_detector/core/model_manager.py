"""Dynamic spaCy model management for Presidio integration.

This module handles automatic detection, installation, and management of spaCy models
without hardcoding versions or model sizes. It provides flexible model installation
and graceful degradation when models are not available.
"""

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# Default models by language (size preference: small -> medium -> large)
DEFAULT_MODELS = {
    "en": ["en_core_web_sm", "en_core_web_md", "en_core_web_lg"],
    "es": ["es_core_news_sm", "es_core_news_md", "es_core_news_lg"],
    "de": ["de_core_news_sm", "de_core_news_md", "de_core_news_lg"],
    "fr": ["fr_core_news_sm", "fr_core_news_md", "fr_core_news_lg"],
    "it": ["it_core_news_sm", "it_core_news_md", "it_core_news_lg"],
    "pt": ["pt_core_news_sm", "pt_core_news_md", "pt_core_news_lg"],
    "nl": ["nl_core_news_sm", "nl_core_news_md", "nl_core_news_lg"],
    "zh": ["zh_core_web_sm", "zh_core_web_md", "zh_core_web_lg"],
    "ja": ["ja_core_news_sm", "ja_core_news_md", "ja_core_news_lg"],
}


class SpacyModelManager:
    """Manages spaCy model installation and detection."""

    def __init__(self):
        """Initialize the model manager."""
        self.spacy_available = False
        self.installed_models = []
        self._check_spacy_availability()

    def _check_spacy_availability(self) -> None:
        """Check if spaCy is available."""
        try:
            import spacy  # noqa: F401

            self.spacy_available = True
            self.installed_models = self._get_installed_models()
            logger.info(f"spaCy available. Installed models: {self.installed_models}")
        except ImportError:
            logger.warning("spaCy not available")

    def _get_installed_models(self) -> list[str]:
        """Get list of installed spaCy models."""
        if not self.spacy_available:
            return []

        try:
            import spacy

            return list(spacy.util.get_installed_models())
        except Exception as e:
            logger.error(f"Error getting installed models: {e}")
            return []

    def get_best_model(
        self, language: str = "en", preferred_size: str = "sm"
    ) -> str | None:
        """Get the best available model for a language.

        Args:
            language: Language code (e.g., 'en', 'es', 'de')
            preferred_size: Preferred model size ('sm', 'md', 'lg')

        Returns:
            Model name if available, None otherwise

        """
        if not self.spacy_available:
            return None

        # Get possible models for the language
        possible_models = DEFAULT_MODELS.get(language, [])
        if not possible_models:
            logger.warning(f"No known models for language: {language}")
            return None

        # Reorder based on size preference
        if preferred_size == "lg":
            possible_models = (
                [m for m in possible_models if "_lg" in m]
                + [m for m in possible_models if "_md" in m]
                + [m for m in possible_models if "_sm" in m]
            )
        elif preferred_size == "md":
            possible_models = (
                [m for m in possible_models if "_md" in m]
                + [m for m in possible_models if "_sm" in m]
                + [m for m in possible_models if "_lg" in m]
            )
        # Default: prefer small models

        # Find first available model
        for model in possible_models:
            if model in self.installed_models:
                logger.info(f"Using installed model: {model}")
                return model

        # No installed model found
        logger.warning(f"No installed models found for language {language}")
        return None

    def install_model(self, model_name: str, force: bool = False) -> bool:
        """Install a spaCy model.

        Args:
            model_name: Name of the model to install
            force: Force installation even if already installed

        Returns:
            True if installation successful, False otherwise

        """
        if not self.spacy_available:
            logger.error("spaCy not available, cannot install models")
            return False

        if not force and model_name in self.installed_models:
            logger.info(f"Model {model_name} already installed")
            return True

        try:
            logger.info(f"Installing spaCy model: {model_name}")

            # Try multiple installation methods
            success = False

            # Method 1: Try uv add with model URL (for uv environments)
            if self._is_uv_environment():
                success = self._install_with_uv(model_name)

            # Method 2: Fall back to spacy download if uv fails
            if not success:
                success = self._install_with_spacy_download(model_name)

            # Method 3: Last resort - try pip if available
            if not success:
                success = self._install_with_pip(model_name)

            if success:
                logger.info(f"Successfully installed model: {model_name}")
                self.installed_models = self._get_installed_models()  # Refresh list
                return True
            else:
                logger.error(f"Failed to install model {model_name} using all methods")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing model {model_name}")
            return False
        except Exception as e:
            logger.error(f"Error installing model {model_name}: {e}")
            return False

    def _is_uv_environment(self) -> bool:
        """Check if we're running in a uv environment."""
        # Check if uv is available and if we're in a uv project
        try:
            # Look for uv.lock file or .venv created by uv
            import os

            current_dir = os.getcwd()
            return os.path.exists(
                os.path.join(current_dir, "uv.lock")
            ) or os.path.exists(os.path.join(current_dir, "pyproject.toml"))
        except Exception:
            return False

    def _get_spacy_version(self) -> str:
        """Get the installed spaCy version."""
        try:
            import spacy

            return spacy.__version__
        except Exception:
            return "3.8.0"  # Default fallback version

    def _get_model_url(self, model_name: str) -> str | None:
        """Get the GitHub URL for a spaCy model based on current spaCy version."""
        spacy_version = self._get_spacy_version()

        # Map of major spaCy versions to model versions
        version_map = {
            "3.8": "3.8.0",
            "3.7": "3.7.1",
            "3.6": "3.6.1",
            "3.5": "3.5.0",
            "3.4": "3.4.4",
        }

        # Get major.minor version
        major_minor = ".".join(spacy_version.split(".")[:2])
        model_version = version_map.get(major_minor, spacy_version)

        # Base URL pattern
        base_url = "https://github.com/explosion/spacy-models/releases/download"

        # Common models with predictable naming
        model_patterns = [
            "en_core_web_sm",
            "en_core_web_md",
            "en_core_web_lg",
            "es_core_news_sm",
            "es_core_news_md",
            "es_core_news_lg",
            "de_core_news_sm",
            "de_core_news_md",
            "de_core_news_lg",
            "fr_core_news_sm",
            "fr_core_news_md",
            "fr_core_news_lg",
            "it_core_news_sm",
            "it_core_news_md",
            "it_core_news_lg",
            "pt_core_news_sm",
            "pt_core_news_md",
            "pt_core_news_lg",
            "nl_core_news_sm",
            "nl_core_news_md",
            "nl_core_news_lg",
            "zh_core_web_sm",
            "zh_core_web_md",
            "zh_core_web_lg",
            "ja_core_news_sm",
            "ja_core_news_md",
            "ja_core_news_lg",
        ]

        if model_name in model_patterns:
            return f"{base_url}/{model_name}-{model_version}/{model_name}-{model_version}-py3-none-any.whl"
        else:
            logger.warning(f"Unknown model pattern: {model_name}")
            return None

    def _install_with_uv(self, model_name: str) -> bool:
        """Install model using uv add with direct URL."""
        try:
            model_url = self._get_model_url(model_name)
            if not model_url:
                logger.warning(f"Cannot determine URL for model {model_name}")
                return False

            # Use uv add to install from URL
            cmd = ["uv", "add", f"{model_name}@{model_url}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(f"Successfully installed {model_name} with uv")
                return True
            else:
                logger.warning(
                    f"uv installation failed for {model_name}: {result.stderr}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error installing {model_name} with uv: {e}")
            return False

    def _install_with_spacy_download(self, model_name: str) -> bool:
        """Install model using spacy download command."""
        try:
            cmd = [sys.executable, "-m", "spacy", "download", model_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(f"Successfully installed {model_name} with spacy download")
                return True
            else:
                logger.warning(
                    f"spacy download failed for {model_name}: {result.stderr}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error installing {model_name} with spacy download: {e}")
            return False

    def _install_with_pip(self, model_name: str) -> bool:
        """Install model using pip (fallback method)."""
        try:
            # First check if pip is available
            pip_cmd = [sys.executable, "-m", "pip", "--version"]
            pip_check = subprocess.run(
                pip_cmd, capture_output=True, text=True, timeout=10
            )

            if pip_check.returncode != 0:
                logger.warning("pip not available, cannot install with pip")
                return False

            # Get model URL
            model_url = self._get_model_url(model_name)
            if not model_url:
                logger.warning(f"Cannot determine URL for model {model_name}")
                return False

            # Try to install with pip
            cmd = [sys.executable, "-m", "pip", "install", model_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(f"Successfully installed {model_name} with pip")
                return True
            else:
                logger.warning(
                    f"pip installation failed for {model_name}: {result.stderr}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error installing {model_name} with pip: {e}")
            return False

    def install_default_model(
        self, language: str = "en", preferred_size: str = "sm"
    ) -> str | None:
        """Install and return the best default model for a language.

        Args:
            language: Language code
            preferred_size: Preferred model size

        Returns:
            Installed model name if successful, None otherwise

        """
        if not self.spacy_available:
            return None

        # Check if we already have a good model
        existing_model = self.get_best_model(language, preferred_size)
        if existing_model:
            return existing_model

        # Try to install models in preference order
        possible_models = DEFAULT_MODELS.get(language, [])
        if not possible_models:
            return None

        # Reorder based on size preference
        if preferred_size == "lg":
            install_order = (
                [m for m in possible_models if "_lg" in m]
                + [m for m in possible_models if "_md" in m]
                + [m for m in possible_models if "_sm" in m]
            )
        elif preferred_size == "md":
            install_order = (
                [m for m in possible_models if "_md" in m]
                + [m for m in possible_models if "_sm" in m]
                + [m for m in possible_models if "_lg" in m]
            )
        else:  # Default: prefer small models
            install_order = (
                [m for m in possible_models if "_sm" in m]
                + [m for m in possible_models if "_md" in m]
                + [m for m in possible_models if "_lg" in m]
            )

        # Try to install in order
        for model in install_order:
            if self.install_model(model):
                return model

        logger.error(f"Failed to install any model for language {language}")
        return None

    def ensure_model_available(
        self, language: str = "en", preferred_size: str = "sm"
    ) -> str | None:
        """Ensure a model is available, installing if necessary.

        Args:
            language: Language code
            preferred_size: Preferred model size

        Returns:
            Available model name if successful, None otherwise

        """
        # First check if we already have a good model
        existing_model = self.get_best_model(language, preferred_size)
        if existing_model:
            return existing_model

        # Try to install a suitable model
        logger.info(f"No suitable {language} model found, attempting installation...")
        return self.install_default_model(language, preferred_size)

    def get_model_info(self, model_name: str) -> dict[str, str]:
        """Get information about a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model information

        """
        if not self.spacy_available or model_name not in self.installed_models:
            return {"status": "not_available"}

        try:
            import spacy

            nlp = spacy.load(model_name)
            return {
                "status": "available",
                "name": model_name,
                "language": nlp.lang,
                "version": nlp.meta.get("version", "unknown"),
                "size": "sm"
                if "_sm" in model_name
                else "md"
                if "_md" in model_name
                else "lg",
                "components": list(nlp.pipe_names),
            }
        except Exception as e:
            logger.error(f"Error getting info for model {model_name}: {e}")
            return {"status": "error", "error": str(e)}

    def get_available_languages(self) -> list[str]:
        """Get list of languages for which models are available.

        Returns:
            List of language codes

        """
        return list(DEFAULT_MODELS.keys())

    def cleanup_unused_models(self, keep_languages: list[str] | None = None) -> None:
        """Remove unused spaCy models to save space.

        Args:
            keep_languages: Languages to keep models for (None = keep all)

        """
        if not self.spacy_available or not keep_languages:
            return

        models_to_remove = []
        for model in self.installed_models:
            model_lang = model.split("_")[0]  # Extract language from model name
            if model_lang not in keep_languages:
                models_to_remove.append(model)

        for model in models_to_remove:
            try:
                logger.info(f"Removing unused model: {model}")

                # Try uv remove first if in uv environment
                success = False
                if self._is_uv_environment():
                    try:
                        cmd = ["uv", "remove", model]
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=60
                        )
                        if result.returncode == 0:
                            success = True
                            logger.info(f"Successfully removed {model} with uv")
                    except Exception as e:
                        logger.warning(f"uv remove failed for {model}: {e}")

                # Fall back to pip if uv didn't work
                if not success:
                    try:
                        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", model]
                        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        logger.info(f"Successfully removed {model} with pip")
                    except Exception as e:
                        logger.error(f"Error removing model {model}: {e}")

            except Exception as e:
                logger.error(f"Error removing model {model}: {e}")

        # Refresh installed models list
        self.installed_models = self._get_installed_models()


# Global instance
_model_manager = None


def get_model_manager() -> SpacyModelManager:
    """Get or create the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = SpacyModelManager()
    return _model_manager


def ensure_spacy_model(language: str = "en", preferred_size: str = "sm") -> str | None:
    """Ensure a spaCy model is available.

    Args:
        language: Language code
        preferred_size: Preferred model size

    Returns:
        Available model name if successful, None otherwise

    """
    manager = get_model_manager()
    return manager.ensure_model_available(language, preferred_size)


def get_best_spacy_model(
    language: str = "en", preferred_size: str = "sm"
) -> str | None:
    """Get the best available spaCy model.

    Args:
        language: Language code
        preferred_size: Preferred model size

    Returns:
        Model name if available, None otherwise

    """
    manager = get_model_manager()
    return manager.get_best_model(language, preferred_size)


def install_spacy_model(model_name: str, force: bool = False) -> bool:
    """Install a spaCy model.

    Args:
        model_name: Name of the model to install
        force: Force installation even if already installed

    Returns:
        True if installation successful, False otherwise

    """
    manager = get_model_manager()
    return manager.install_model(model_name, force)
