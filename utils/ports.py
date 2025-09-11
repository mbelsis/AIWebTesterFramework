"""
Port utility functions for the AI WebTester framework.

Provides automatic port detection to avoid port conflicts in development environments.
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def find_free_port(start: int = 5000, max_attempts: int = 100) -> int:
    """
    Find an available port starting from the preferred port number.
    
    Args:
        start: Preferred starting port number (default: 5000)
        max_attempts: Maximum number of ports to try before giving up (default: 100)
        
    Returns:
        int: Available port number
        
    Raises:
        RuntimeError: If no free port is found within max_attempts
    """
    for port in range(start, start + max_attempts):
        if is_port_available(port):
            logger.info(f"Found available port: {port}")
            return port
    
    raise RuntimeError(f"No free port found in range {start}-{start + max_attempts - 1}")


def is_port_available(port: int) -> bool:
    """
    Check if a specific port is available for binding.
    
    Args:
        port: Port number to check
        
    Returns:
        bool: True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
            return True
    except OSError as e:
        logger.debug(f"Port {port} is not available: {e}")
        return False


def find_free_port_range(start: int, count: int = 2) -> list[int]:
    """
    Find multiple consecutive free ports starting from a preferred port.
    
    Args:
        start: Starting port number
        count: Number of consecutive ports needed
        
    Returns:
        list[int]: List of available consecutive port numbers
        
    Raises:
        RuntimeError: If consecutive ports cannot be found
    """
    max_attempts = 100
    for base_port in range(start, start + max_attempts - count + 1):
        ports = list(range(base_port, base_port + count))
        if all(is_port_available(port) for port in ports):
            logger.info(f"Found {count} consecutive ports starting from: {base_port}")
            return ports
    
    raise RuntimeError(f"Could not find {count} consecutive free ports starting from {start}")


def get_service_url(host: str = "127.0.0.1", port: int = 5000, https: bool = False) -> str:
    """
    Generate a service URL from host and port.
    
    Args:
        host: Hostname or IP address
        port: Port number  
        https: Whether to use HTTPS (default: False)
        
    Returns:
        str: Complete service URL
    """
    protocol = "https" if https else "http"
    return f"{protocol}://{host}:{port}"