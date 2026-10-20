import os
import struct
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from controllers import system_controller


class SystemWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.temp_dir.name, 'data'))
        self.config_path = os.path.join(self.temp_dir.name, 'data', 'config.cfg')
        with open(self.config_path, 'w') as config_file:
            config_file.write('WATCHDOG_ENABLED=False\nWATCHDOG_TIMEOUT=60\n')

        self.system = system_controller.System.__new__(system_controller.System)
        self.system.app = SimpleNamespace(
            root_path=self.temp_dir.name,
            config={'WATCHDOG_TIMEOUT': 60, 'WATCHDOG_ENABLED': False},
            logger=SimpleNamespace(exception=lambda *args: None))
        self.system.watchdog_lock = threading.Lock()
        self.system.watchdog_fd = None
        self.system.watchdog_healthy = None
        self.system.watchdog_module_loaded_by_app = False

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_enable_healthy_reset_and_disable(self):
        def ioctl(fd, request, argument, mutate=False):
            if request == system_controller.WDIOC_SETTIMEOUT:
                struct.pack_into('i', argument, 0, 60)

        with patch.object(self.system, '_get_runtime_watchdog_usec', return_value=0), \
                patch.object(self.system, '_watchdog_device', return_value='/dev/watchdog0'), \
            patch.object(self.system, '_load_watchdog_module'), \
            patch.object(self.system, '_unload_watchdog_module') as unload_module, \
                patch.object(system_controller.os, 'open', return_value=42), \
                patch.object(system_controller.os, 'write', return_value=1) as write, \
                patch.object(system_controller.os, 'close') as close, \
                patch.object(system_controller.fcntl, 'ioctl', side_effect=ioctl):
            self.assertTrue(self.system.set_watchdog_enabled(True))
            self.assertTrue(self.system.is_watchdog_enabled())
            self.assertTrue(self.system.reset_watchdog(True))
            self.assertFalse(self.system.reset_watchdog(False))
            self.assertFalse(self.system.set_watchdog_enabled(False))

        self.assertEqual(write.call_args_list[0].args, (42, b'\0'))
        self.assertEqual(write.call_count, 1)
        close.assert_called_once_with(42)
        unload_module.assert_called_once_with()
        with open(self.config_path) as config_file:
            self.assertIn('WATCHDOG_ENABLED=False\n', config_file.readlines())

    def test_enable_fails_if_systemd_watchdog_is_active(self):
        with patch.object(self.system, '_get_runtime_watchdog_usec', return_value=60000000), \
                patch.object(system_controller.os, 'open') as open_device:
            with self.assertRaisesRegex(RuntimeError, 'RuntimeWatchdogSec is active'):
                self.system.set_watchdog_enabled(True)

        open_device.assert_not_called()

    def test_reset_requires_enabled_watchdog(self):
        with self.assertRaisesRegex(RuntimeError, 'not enabled'):
            self.system.reset_watchdog(True)

    def test_unhealthy_heartbeat_does_not_implicitly_activate(self):
        self.system.app.config['WATCHDOG_ENABLED'] = True
        with patch.object(self.system, '_activate_watchdog_locked') as activate:
            self.assertFalse(self.system.reset_watchdog(False))

        activate.assert_not_called()

    def test_healthy_heartbeat_implicitly_activates_if_configured(self):
        self.system.app.config['WATCHDOG_ENABLED'] = True

        def activate():
            self.system.watchdog_fd = 42

        with patch.object(self.system, '_activate_watchdog_locked', side_effect=activate) as activate_mock, \
                patch.object(system_controller.os, 'write', return_value=1) as write:
            self.assertTrue(self.system.reset_watchdog(True))

        activate_mock.assert_called_once_with()
        write.assert_called_once_with(42, b'\0')

    def test_stop_session_does_not_change_persistent_setting(self):
        self.system.app.config['WATCHDOG_ENABLED'] = True
        self.system.watchdog_fd = 42
        with patch.object(self.system, '_deactivate_watchdog') as deactivate, \
                patch.object(self.system, '_unload_watchdog_module'):
            self.system.stop_watchdog_session()

        deactivate.assert_called_once_with(42)
        self.assertFalse(self.system.is_watchdog_enabled())
        self.assertTrue(self.system.is_watchdog_configured())

    def test_watchdog_device_falls_back_to_any_numbered_device(self):
        with patch.object(system_controller.os.path, 'exists', return_value=False), \
                patch.object(system_controller.glob, 'glob', return_value=['/dev/watchdog1']):
            self.assertEqual(self.system._watchdog_device(), '/dev/watchdog1')
    
    def test_loads_module_only_when_not_already_loaded(self):
        with patch.object(system_controller.os.path, 'exists', return_value=False), \
                patch.object(system_controller, 'check_call') as check_call:
            self.system._load_watchdog_module()
        
        check_call.assert_called_once_with(['modprobe', 'iTCO_wdt'])
        self.assertTrue(self.system.watchdog_module_loaded_by_app)
    
    def test_does_not_claim_preloaded_module(self):
        with patch.object(system_controller.os.path, 'exists', return_value=True), \
                patch.object(system_controller, 'check_call') as check_call:
            self.system._load_watchdog_module()
        
        check_call.assert_not_called()
        self.assertFalse(self.system.watchdog_module_loaded_by_app)

    def test_invalid_health_state_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'boolean'):
            self.system.reset_watchdog('unknown')

    def test_timeout_mismatch_closes_device(self):
        def ioctl(fd, request, argument, mutate=False):
            if request == system_controller.WDIOC_SETTIMEOUT:
                struct.pack_into('i', argument, 0, 30)

        with patch.object(self.system, '_get_runtime_watchdog_usec', return_value=0), \
                patch.object(self.system, '_watchdog_device', return_value='/dev/watchdog0'), \
            patch.object(self.system, '_load_watchdog_module'), \
            patch.object(self.system, '_unload_watchdog_module'), \
                patch.object(system_controller.os, 'open', return_value=42), \
                patch.object(system_controller.os, 'close') as close, \
                patch.object(system_controller.fcntl, 'ioctl', side_effect=ioctl):
            with self.assertRaisesRegex(RuntimeError, 'not 60 seconds'):
                self.system.set_watchdog_enabled(True)

        self.assertFalse(self.system.is_watchdog_enabled())
        close.assert_called_once_with(42)


if __name__ == '__main__':
    unittest.main()