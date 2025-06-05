import os
import platform
import signal

import psutil

import logging
import ctypes

logger = logging.getLogger(__name__)

def hide_drivers_command_prompt():
    logger.info('Hide drivers')
    if 'Windows' in platform.system():
        import win32gui

        def enum_window_step(hwnd, windowList):
            win_name = win32gui.GetWindowText(hwnd)
            win_class_name = win32gui.GetClassName(hwnd)
            if 'chromedriver' in win_name.lower() or 'chromedriver' in win_class_name.lower():
                win32gui.ShowWindow(hwnd, False)

        win32gui.EnumWindows(enum_window_step, [])

class ProcessKiller:
    def __init__(self):
        pass

    def kill(self, browser_pid):
        logger.info(f'Killing process {browser_pid}')
        print(browser_pid)
        if type(browser_pid) is list:
            logger.info('is list process')
            for pid in browser_pid:
                logger.info(f'Killing process {pid}')
                if pid > 0:
                    logger.info('more than 0 process')
                    try:
                        logger.info('try to kill process')
                        process = psutil.Process(pid)
                        for child_proc in process.children(recursive=True):
                            try:
                                child_proc.kill()
                            except Exception as ex:
                                logger.exception(ex)
                        process.kill()

                        process.wait(timeout=30)

                        logger.info('process terminated')
                    except psutil.NoSuchProcess:
                        logger.info('process not found')
                        logger.warning(f'process {pid} not found')
                    except Exception as ex:
                        logger.info('exception')
                        logger.exception(ex)

        else:
            if browser_pid > 0:
                try:
                    process = psutil.Process(browser_pid)
                    for child_proc in process.children(recursive=True):
                        try:
                            child_proc.kill()
                        except Exception as ex:
                            logger.exception(ex)
                    process.kill()

                    process.wait(timeout=30)

                    logger.info('process terminated')
                except psutil.NoSuchProcess:
                    logger.warning(f'process {browser_pid} not found')
                except Exception as ex:
                    logger.exception(ex)
