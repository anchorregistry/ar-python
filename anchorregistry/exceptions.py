# SPDX-License-Identifier: BUSL-1.1
"""Custom exceptions for anchorregistry."""


class AnchorNotFoundError(Exception):
    """Raised when an AR-ID does not exist on-chain."""


class ConfigurationError(Exception):
    """Raised when the package is used before a contract address is available."""
