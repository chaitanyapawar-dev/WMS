"""Request contracts for the inbound receiving voice preview endpoint."""

from enum import Enum


class VoiceWorkflow(str, Enum):
    """Restrict voice processing to the explicitly supported WMS workflow."""

    RECEIVING = "receiving"
