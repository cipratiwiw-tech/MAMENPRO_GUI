def run_ffmpeg_thread(self):
        """Thread Render STABIL: Menghindari pipe blocking dan menampilkan log error"""
        import traceback
        output_filename = "MAMENPRO_RENDER_FINAL.mp4"
        
        try:
            # 1. Pastikan Dimensi Genap (Wajib untuk H.264)
            w = int(self.canvas.canvas_rect.width())
            h = int(self.canvas.canvas_rect.height())
            if w % 2 != 0: w += 1
            if h % 2 != 0: h += 1

            fps = 30
            duration = self.timeline.duration
            total_frames = int(duration * fps)
            
            print(f"🚀 Render Start: {w}x{h} @ {fps}fps | {total_frames} frames")
            
            if total_frames <= 0:
                print("❌ Error: Total frames 0. Periksa timeline!")
                return

            # 2. Setup Command FFmpeg
            # PENTING: stderr=None agar log FFmpeg langsung keluar ke terminal Anda (CMD/VSCode)
            command = [
                'ffmpeg', '-y',
                '-f', 'rawvideo', '-vcodec', 'rawvideo',
                '-s', f'{w}x{h}',
                '-pix_fmt', 'bgra', 
                '-r', str(fps),
                '-i', '-', 
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-crf', '23',
                output_filename
            ]

            # 3. Jalankan FFmpeg
            # Gunakan stderr=None atau sys.stderr agar tidak terjadi DEADLOCK
            process = subprocess.Popen(
                command, 
                stdin=subprocess.PIPE, 
                stderr=None,  # JANGAN GUNAKAN subprocess.PIPE jika tidak dibaca
                bufsize=10**8,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )

            # 4. Loop Frame
            for i in range(total_frames):
                if self.is_rendering_stopped:
                    print("🛑 Render stopped by user.")
                    break

                t = i / fps
                frame = self.timeline.get_frame(t)

                # ✅ BACKGROUND ENGINE (JIKA ADA)
                if hasattr(self, "bg_layer") and self.bg_layer:
                    frame = self.bg_layer.render(frame, i, fps)

                
                # Jika engine gagal ambil frame, buat frame hitam
                if frame is None:
                    frame = np.zeros((h, w, 4), dtype=np.uint8)
                
                # Pastikan format BGRA (4 channel) sesuai input -pix_fmt bgra
                if frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                
                # Resize paksa jika ada selisih resolusi
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, (w, h))

                # Tulis ke pipa
                try:
                    process.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    print("🔥 FFmpeg berhenti mendadak (Broken Pipe). Periksa log di atas!")
                    break

                if i % 15 == 0:
                    percent = int((i / total_frames) * 100)
                    QMetaObject.invokeMethod(self, "set_render_status", Qt.QueuedConnection, 
                                            Q_ARG(bool, True), Q_ARG(int, percent), Q_ARG(str, f"Frame {i}"))

            # 5. Tutup Pipa
            process.stdin.close()
            process.wait()
            print(f"✅ Render Selesai: {output_filename}")

        except Exception as e:
            print("🔥 CRITICAL RENDER ERROR:")
            traceback.print_exc() # Menampilkan baris error secara detail
        finally:
            QMetaObject.invokeMethod(self, "set_render_status", Qt.QueuedConnection, 
                                     Q_ARG(bool, False), Q_ARG(int, 100), Q_ARG(str, "Done"))