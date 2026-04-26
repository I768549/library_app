import threading
import queue


class ThreadWorker:
    """Запускає функцію у фоновому потоці та повертає результат у GUI-потік
    через threading.Queue + root.after().
    Кожен виклик run() створює власну чергу
    """

    def __init__(self, root):
        self.root = root

    def run(self, func, *args, on_start=None, on_done=None, on_error=None):
        if on_start:
            on_start()

        q = queue.Queue()

        def target():
            try:
                result = func(*args)
                q.put(("done", result))
            except Exception as exc:
                q.put(("error", exc))

        threading.Thread(target=target, daemon=True).start()
        self.root.after(100, lambda: self._check(q, on_done, on_error))

    def _check(self, q, on_done, on_error):
        try:
            kind, data = q.get_nowait()
        except queue.Empty:
            self.root.after(100, lambda: self._check(q, on_done, on_error))
            return

        if kind == "done":
            if on_done:
                on_done(data)
        else:
            if on_error:
                on_error(data)
