"""
pihole/manager.py

This module defines the PiHoleManager class for managing multiple Pi-hole instances in parallel.
It provides utilities for performing parallel operations (status polling, blocking toggling)
 across all managed instances with reusable threading logic.

Classes:
    PiHoleManager: Manages multiple Pi-hole API instances and parallelizes actions across them.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from .v6 import PiHoleV6API

class PiHoleManager:
    """
    Manages multiple Pi-hole instances and abstracts API version handling.
    Provides parallel operations for status checks and blocking toggling.

    Args:
        instances_config (dict): A mapping of instance names to instance configuration dictionaries.
    """

    def __init__(self, instances_config):
        """
        Initialize the PiHoleManager with instances configuration.

        Args:
            instances_config (dict): Mapping of instance names to config dicts.
        """
        self.instances = {}
        for name, conf in instances_config.items():
            api_version = conf.get("api_version", "v6")
            if api_version == "v6":
                self.instances[name] = PiHoleV6API(conf["domain"], conf["token"])
            else:
                raise NotImplementedError(f"API version {api_version} not supported")

    def _parallel_map(self, func, *args_for_func):
        """
        Helper to run func(instance, *args) for each instance in parallel.

        Args:
            func (callable): Function to apply to each instance.
            *args_for_func: Additional arguments to pass to func.

        Returns:
            list: List of (name, result) tuples.
        """
        results = []
        with ThreadPoolExecutor(max_workers=min(10, len(self.instances))) as executor:
            future_to_name = {
                executor.submit(func, inst, *args_for_func): name
                for name, inst in self.instances.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                except TimeoutError:
                    result = None
                except Exception as e: # pylint: disable=broad-except
                    print(f"Failure encountered: {e}")
                    result = None
                results.append((name, result))
        return results

    def get_statuses(self):
        """
        Retrieve the blocking status for all managed Pi-hole instances in parallel.

        Returns:
            list: List of (name, status) tuples for each instance.
        """
        def _get_status(instance):
            return instance.get_blocking_status()
        return self._parallel_map(_get_status)

    def set_blocking_all(self, enable: bool, duration=None):
        """
        Enable or disable blocking on all managed Pi-hole instances in parallel.

        Args:
            enable (bool): True to enable blocking, False to disable.
            duration (optional): Duration for temporary blocking (if supported).

        Returns:
            list: List of (name, ok, msg) tuples with result for each instance.
        """
        def _set_blocking(instance, enable, duration):
            return instance.set_blocking(enable, duration)
        raw_results = self._parallel_map(_set_blocking, enable, duration)
        return [(name, *(result if isinstance(result, tuple) else (False, "Error")))
                for name, result in raw_results]
