import atexit
import contextlib
import os


class OpmonPidFileHandler:
    def __init__(self, settings):
        self.pid_file = os.path.join(
            settings['collector']['pid-directory'],
            f"xroad_metrics_collector_{settings['xroad']['instance']}.pid"
        )

        self.file_created = False

        atexit.register(self._cleanup)

    @staticmethod
    def pid_exists(pid: int):
        if pid < 0:
            return False

        try:
            os.kill(pid, 0)  # Signal 0 does nothing
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # Operation not permitted (i.e., process exists)
        else:
            return True

    def another_instance_is_running(self):
        if os.path.isfile(self.pid_file):
            with open(self.pid_file, 'r') as f:
                try:
                    pid = int(f.readline())
                    if self.pid_exists(pid):
                        return True
                except (TypeError, ValueError):
                    pass

            os.remove(self.pid_file)
        return False

    def create_pid_file(self):
        if self.another_instance_is_running():
            raise RuntimeError(f"Found PID-file {self.pid_file}. Another opmon-collector instance is already running.")

        os.makedirs(os.path.dirname(self.pid_file), exist_ok=True)

        pid = os.getpid()
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        self.file_created = True

    def _cleanup(self):
        if self.file_created:
            with contextlib.suppress(FileNotFoundError):
                os.remove(self.pid_file)
