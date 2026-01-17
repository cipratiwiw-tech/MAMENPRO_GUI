import copy
from PySide6.QtCore import QObject, Signal, QThread
from manager.timeline.timeline_engine import TimelineEngine
from engine.ffmpeg_renderer import FFmpegRenderer
from engine.compositor import Compositor


class RenderWorker(QThread):
    sig_progress = Signal(int)
    sig_finished = Signal(bool, str)
    sig_log = Signal(str)

    def __init__(self, timeline: TimelineEngine, config: dict, video_service):
        super().__init__()
        self.timeline = timeline
        self.config = config
        self.video_service = video_service
        self.is_running = True

    def run(self):
        try:
            compositor = Compositor()

            output_path = self.config["path"]
            width = self.config["width"]
            height = self.config["height"]
            fps = self.config["fps"]

            renderer = FFmpegRenderer(width, height, fps)
            renderer.start_process(output_path)

            total_duration = self.timeline.get_active_duration()  # seconds
            total_frames = int(total_duration * fps)

            self.sig_log.emit(
                f"🎬 Rendering {total_frames} frames @ {fps} FPS"
            )

            for i in range(total_frames):
                if not self.is_running:
                    renderer.close_process()
                    self.sig_finished.emit(False, "Cancelled")
                    return

                t = i / float(fps)  # seconds (SINGLE SOURCE OF TRUTH)

                active_layers = self.timeline.get_active_layers(t)
                frame = compositor.compose(
                    t, active_layers, width, height
                )

                if frame is not None:
                    renderer.write_frame(frame)

                if i % 10 == 0 and total_frames > 0:
                    self.sig_progress.emit(int(i / total_frames * 100))

            renderer.close_process()
            self.sig_progress.emit(100)
            self.sig_finished.emit(True, output_path)

        except Exception as e:
            self.sig_finished.emit(False, str(e))

    def stop(self):
        self.is_running = False


class RenderService(QObject):
    """
    Service facade untuk render final.
    """

    def start_render_process(self, timeline, config, video_service):
        if not timeline:
            return False, "Timeline is None"
        if not config.get("fps"):
            return False, "Export Error: FPS is missing"
        if not config.get("path"):
            return False, "Export Error: Output path missing"

        # SNAPSHOT TIMELINE (SECONDS, READ-ONLY)
        snapshot = TimelineEngine()
        if hasattr(timeline, "layers"):
            for layer in timeline.layers:
                snapshot.add_layer(copy.deepcopy(layer))

        worker = RenderWorker(snapshot, config, video_service)
        return True, worker
