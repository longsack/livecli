import unittest

import os.path
import livecli_cli.main

from livecli import Livecli
from livecli.compat import is_win32

try:
    from unittest.mock import patch, ANY
except ImportError:
    from mock import patch, ANY

PluginPath = os.path.join(os.path.dirname(__file__), "plugins")


def setup_livecli():
    livecli_cli.main.livecli = Livecli()
    livecli_cli.main.livecli.load_plugins(PluginPath)
    return livecli_cli.main.livecli


class TestCommandLineInvocation(unittest.TestCase):
    """
    Test that when invoked for the command line arguments are parsed as expected
    """

    @patch('livecli_cli.main.CONFIG_FILES', ["/dev/null"])
    @patch('livecli_cli.main.setup_livecli', side_effect=setup_livecli)
    @patch('subprocess.Popen')
    @patch('sys.argv')
    def _test_args(self, args, commandline, mock_argv, mock_popen, mock_setup_livecli, passthrough=False, exit_code=0):
        mock_argv.__getitem__.side_effect = lambda x: args[x]

        def side_effect(results):
            def fn(*args):
                result = results.pop(0)
                return result
            return fn

        mock_popen().poll.side_effect = side_effect([None, 0])

        actual_exit_code = 0
        try:
            livecli_cli.main.main()
        except SystemExit as exc:
            actual_exit_code = exc.code

        self.assertEqual(exit_code, actual_exit_code)
        mock_setup_livecli.assert_called_with()
        if not passthrough:
            mock_popen.assert_called_with(commandline, stderr=ANY, stdout=ANY, bufsize=ANY, stdin=ANY)
        else:
            mock_popen.assert_called_with(commandline, stderr=ANY, stdout=ANY)

    #
    # POSIX tests
    #

    @unittest.skipIf(is_win32, "test only applicable in a POSIX OS")
    def test_open_regular_path_player(self):
        self._test_args(["livecli", "-p", "/usr/bin/vlc", "http://test.se", "test"],
                        ["/usr/bin/vlc", "-"])

    @unittest.skipIf(is_win32, "test only applicable in a POSIX OS")
    def test_open_space_path_player(self):
        self._test_args(["livecli", "-p", "\"/Applications/Video Player/VLC/vlc\"", "http://test.se", "test"],
                        ["/Applications/Video Player/VLC/vlc", "-"])
        # escaped
        self._test_args(["livecli", "-p", "/Applications/Video\ Player/VLC/vlc", "http://test.se", "test"],
                        ["/Applications/Video Player/VLC/vlc", "-"])

    @unittest.skipIf(is_win32, "test only applicable in a POSIX OS")
    def test_open_player_extra_args_in_player(self):
        self._test_args(["livecli", "-p", "/usr/bin/vlc",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "http://test.se", "test"],
                        ["/usr/bin/vlc", "--input-title-format", 'Poker "Stars"', "-"])

    @unittest.skipIf(is_win32, "test only applicable in a POSIX OS")
    def test_open_player_extra_args_in_player_pass_through(self):
        self._test_args(["livecli", "--player-passthrough", "rtmp", "-p", "/usr/bin/vlc",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "test.se", "rtmp"],
                        ["/usr/bin/vlc", "--input-title-format", 'Poker "Stars"', "rtmp://test.se"],
                        passthrough=True)

    #
    # Windows Tests
    #

    @unittest.skipIf(not is_win32, "test only applicable on Windows")
    def test_open_space_path_player_win32(self):
        self._test_args(["livecli", "-p", "c:\\Program Files\\VideoLAN\VLC\\vlc.exe", "http://test.se", "test"],
                        "c:\\Program Files\\VideoLAN\\VLC\\vlc.exe -")

    @unittest.skipIf(not is_win32, "test only applicable on Windows")
    def test_open_space_quote_path_player_win32(self):
        self._test_args(["livecli", "-p", "\"c:\\Program Files\\VideoLAN\VLC\\vlc.exe\"", "http://test.se", "test"],
                        "\"c:\\Program Files\\VideoLAN\\VLC\\vlc.exe\" -")

    @unittest.skipIf(not is_win32, "test only applicable on Windows")
    def test_open_player_args_with_quote_in_player_win32(self):
        self._test_args(["livecli", "-p",
                         '''c:\\Program Files\\VideoLAN\VLC\\vlc.exe --input-title-format "Poker \\"Stars\\""''',
                         "http://test.se", "test"],
                        '''c:\\Program Files\\VideoLAN\VLC\\vlc.exe --input-title-format "Poker \\"Stars\\"" -''')

    @unittest.skipIf(not is_win32, "test only applicable on Windows")
    def test_open_player_extra_args_in_player_win32(self):
        self._test_args(["livecli", "-p", "c:\\Program Files\\VideoLAN\VLC\\vlc.exe",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "http://test.se", "test"],
                        '''c:\\Program Files\\VideoLAN\VLC\\vlc.exe --input-title-format "Poker \\"Stars\\"" -''')

    @unittest.skipIf(not is_win32, "test only applicable on Windows")
    def test_open_player_extra_args_in_player_pass_through_win32(self):
        self._test_args(["livecli", "--player-passthrough", "rtmp", "-p", "c:\\Program Files\\VideoLAN\VLC\\vlc.exe",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "test.se", "rtmp"],
                        '''c:\\Program Files\\VideoLAN\VLC\\vlc.exe --input-title-format "Poker \\"Stars\\"" \"rtmp://test.se\"''',
                        passthrough=True)


if __name__ == "__main__":
    unittest.main()
