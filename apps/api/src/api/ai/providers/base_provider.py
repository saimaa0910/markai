import abc
from typing import Dict, Any, Optional, Type


class BaseProvider(abc.ABC):
    """
    Base class for all multi-modal service providers (Image, Video, Audio, Speech, 3D).
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the unique provider name."""
        pass

    @abc.abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """Return a mapping of supported capabilities."""
        pass

    @abc.abstractmethod
    def health(self) -> bool:
        """Verify the health status of the provider API/endpoint."""
        pass

    # Standardized visual/auditory tool operations
    def generate(self, **kwargs) -> Any:
        raise NotImplementedError(f"Generation is not implemented for provider '{self.name}'.")

    def edit(self, **kwargs) -> Any:
        raise NotImplementedError(f"Editing is not implemented for provider '{self.name}'.")

    def variation(self, **kwargs) -> Any:
        raise NotImplementedError(f"Variation is not implemented for provider '{self.name}'.")

    def upscale(self, **kwargs) -> Any:
        raise NotImplementedError(f"Upscaling is not implemented for provider '{self.name}'.")


class ProviderRegistry:
    """
    Central registration registry for all multi-modal providers.
    """

    _registry: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseProvider]) -> None:
        """Register a provider class."""
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider_cls(cls, name: str) -> Optional[Type[BaseProvider]]:
        """Retrieve a registered provider class."""
        return cls._registry.get(name.lower())

    @classmethod
    def get_provider(cls, name: str) -> Optional[BaseProvider]:
        """Get an instance of a registered provider."""
        prov_cls = cls.get_provider_cls(name)
        if prov_cls:
            return prov_cls()
        return None

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseProvider]]:
        """List all registered providers."""
        return cls._registry
