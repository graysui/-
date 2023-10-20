# -*- coding: utf-8 -*-

"""
可运行5.0
一个文件监控工具，根据文件类型选择执行复制或创建软链接的操作。
"""
import os
import shutil
import threading
import logging
from time import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 日志配置
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 定义并设置控制台日志处理器
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 定义并设置文件日志处理器
file_handler = logging.FileHandler('monitor_v1_0.log')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

lock = threading.Lock()


class FileMonitorHandler(FileSystemEventHandler):
    """文件监控处理器"""
    processed_files = dict()

    def __init__(self, monpath, sync, **kwargs):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self._watch_path = monpath
        self.sync = sync

    def on_created(self, event):
        """当文件被创建时的处理方法"""
        self.file_change_handler(event)

    def on_modified(self, event):
        """当文件被修改时的处理方法"""
        self.file_change_handler(event)

    def file_change_handler(self, event):
        """处理文件变动事件，如创建、修改等"""

        now = time()
        recent_time = self.processed_files.get(event.src_path, 0)
        if now - recent_time < 1:  # 如果文件已在最近1秒内处理过，则忽略
            return
        self.processed_files[event.src_path] = now  # 更新为最新处理时间

        if not event.is_directory:
            event_path = event.src_path
            try:
                lock.acquire()
                if not os.path.exists(event_path):
                    return
                self.sync.handle_file(event_path)
            except Exception as e:
                logger.error(f"处理 {event_path} 时发生错误：{str(e)}")
            finally:
                lock.release()


class Sync:
    """核心同步类，处理文件变动并根据文件类型选择操作"""

    _observer = []

    def __init__(self, source_path, link_path):
        self.source_path = source_path
        self.link_path = link_path

    def handle_file(self, event_path, retry=False):
        """处理文件，根据文件类型执行复制或创建软链接的操作"""
        file_ext = os.path.splitext(event_path)[1].lower()

        # 针对元数据文件如 nfo、jpg 进行复制
        if file_ext in ['.nfo', '.jpg']:
            target_file = os.path.join(self.link_path, os.path.basename(event_path))

            # 检查目标文件是否已存在
            file_existed = os.path.exists(target_file)

            if file_existed:
                try:
                    os.remove(target_file)
                    logger.info(f"删除了已存在的 {target_file}")
                except Exception as delete_error:
                    logger.error(f"在尝试删除 {target_file} 时发生错误: {str(delete_error)}")

            try:
                shutil.copy2(event_path, target_file)
                if file_existed:
                    logger.info(f"修改了 {target_file}")
                else:
                    logger.info(f"复制了 {event_path} 到 {target_file}")
            except Exception as copy_error:
                logger.error(f"在尝试复制 {event_path} 到 {target_file} 时发生错误: {str(copy_error)}")

        # 针对视频文件如 mkv、mp4 创建软链接
        elif file_ext in ['.mkv', '.mp4']:
            link_name = os.path.join(self.link_path, os.path.basename(event_path))
            try:
                os.symlink(event_path, link_name)
                logger.info(f"为 {event_path} 创建了软链接 {link_name}")
            except Exception as e:
                # 如果软链接已存在，跳过
                if os.path.exists(link_name):
                    logger.info(f"{link_name} 已存在，跳过创建软链接")
                else:
                    logger.error(f"为 {event_path} 创建软链接时发生错误: {str(e)}")

    def run_service(self):
        """启动监控服务"""
        observer = Observer(timeout=10)
        observer.schedule(FileMonitorHandler(self.source_path, self), path=self.source_path, recursive=True)
        observer.daemon = True
        observer.start()
        self._observer.append(observer)
        print(f"开始监控 {self.source_path}")

    def stop_service(self):
        """停止监控服务"""
        for observer in self._observer:
            observer.stop()
            observer.join()
        self._observer = []
        print(f"停止监控 {self.source_path}")


if __name__ == "__main__":
    source_path = "/media/欧美剧"  # 替换为你要监控的路径
    target_link_path = "/media/benji"  # 替换为你想要放置软链接或复制文件的路径

    if not os.path.exists(target_link_path):
        os.makedirs(target_link_path)

    sync = Sync(source_path, target_link_path)
    sync.run_service()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        sync.stop_service()

