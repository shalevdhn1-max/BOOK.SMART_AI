"""Provider-agnostic invoice integration infrastructure.

This module deliberately contains no fake provider API calls.  A real Israeli
invoice provider can be implemented later by subclassing InvoiceProvider and
registering the provider name.
"""
from abc import ABC, abstractmethod


class InvoiceIntegrationError(Exception):
    """Raised when an invoice provider operation cannot be completed."""


class InvoiceProvider(ABC):
    """Contract every real invoice provider adapter must implement."""

    name = "base"

    @abstractmethod
    def test_connection(self, credentials):
        raise NotImplementedError

    @abstractmethod
    def create_invoice(self, business, customer, invoice_data, credentials):
        raise NotImplementedError

    @abstractmethod
    def get_invoice(self, provider_invoice_id, credentials):
        raise NotImplementedError


class ProviderRegistry:
    def __init__(self):
        self._providers = {}

    def register(self, provider):
        self._providers[provider.name] = provider

    def get(self, name):
        return self._providers.get(name)

    def names(self):
        return tuple(sorted(self._providers))


registry = ProviderRegistry()

# Provider names are intentionally configuration slots.  No credentials or
# external requests are performed until a real adapter is supplied.
AVAILABLE_PROVIDER_SLOTS = {
    "generic": "ספק חשבוניות חיצוני",
}
