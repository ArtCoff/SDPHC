from PySide6.QtCore import QRunnable, Signal, QObject


class WorkerSignals(QObject):
    result = Signal(object)  # 传递任务结果
    error = Signal(tuple)  # 传递异常信息
    progress = Signal(int)  # 进度更新


class Worker(QRunnable):
    def __init__(self, task_id):
        super().__init__()
        self.signals = WorkerSignals()
        self.task_id = task_id
        self.is_interrupted = False

    @Slot()
    def run(self):
        try:
            for i in range(1, 6):
                if self.is_interrupted:
                    return
                time.sleep(1)
                self.signals.progress.emit(i * 20)
            self.signals.result.emit(f"任务 {self.task_id} 完成")
        except Exception as e:
            self.signals.error.emit((str(e), traceback.format_exc()))

    def interrupt(self):
        self.is_interrupted = True
