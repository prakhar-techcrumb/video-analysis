import logging
import requests
from typing import List, Dict, Any

from ..models.callback_dto import CallbackDTO

logger = logging.getLogger(__name__)


def process_callbacks(callbacks: List[CallbackDTO], data: Dict[str, Any] = None):
    """
    Process multiple callbacks synchronously.
    
    Args:
        callbacks: List of callback configurations
        data: Analysis data to send to callbacks
        
    Returns:
        List of callback results
    """
    results = []
    for cb in callbacks:
        try:
            result = process_callback(cb, data)
            results.append(result)
        except Exception as e:
            logger.error(f"Callback failed for {cb.get('url', 'unknown')}: {e}")
            results.append({"error": str(e), "callback": cb})
    return results


def process_callback(cb: CallbackDTO, data: Dict[str, Any] = None):
    """
    Process a single callback.
    
    Args:
        cb: Callback configuration dictionary
        data: Analysis data to send
        
    Returns:
        Response from callback URL
    """
    url = cb.get("url")
    headers = cb.get("headers", {})
    method = cb.get("method", "").upper()

    logger.info(f"Processing callback: {method} {url}")
    logger.debug(f"Headers: {headers}")

    if method == "POST":
        return do_post_request(url, headers, data)
    elif method == "GET":
        return do_get_request(url, headers)
    elif method == "PUT":
        return do_put_request(url, headers, data)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


def do_post_request(url: str, headers: Dict[str, str], data: Dict[str, Any]):
    """Send POST request to callback URL."""
    try:
        logger.info(f"Sending POST to {url}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        logger.info(f"POST response status: {response.status_code}")
        
        return {
            "status": response.status_code,
            "url": url,
            "method": "POST",
            "response": response.text,
            "success": response.status_code < 400
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"POST request failed: {e}")
        raise


def do_get_request(url: str, headers: Dict[str, str]):
    """Send GET request to callback URL."""
    try:
        logger.info(f"Sending GET to {url}")
        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"GET response status: {response.status_code}")
        
        return {
            "status": response.status_code,
            "url": url,
            "method": "GET",
            "response": response.text,
            "success": response.status_code < 400
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"GET request failed: {e}")
        raise


def do_put_request(url: str, headers: Dict[str, str], data: Dict[str, Any]):
    """Send PUT request to callback URL."""
    try:
        logger.info(f"Sending PUT to {url}")
        logger.info(f"Headers: {headers}")
        if data:
            logger.info(f"Data: {data}")
        response = requests.put(url, headers=headers, json=data, timeout=30)
        logger.info(f"PUT response status: {response.status_code}")
        
        return {
            "status": response.status_code,
            "url": url,
            "method": "PUT", 
            "response": response.text,
            "success": response.status_code < 400
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"PUT request failed: {e}")
        raise