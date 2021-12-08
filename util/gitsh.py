#!/usr/bin/env python3
# @Date    : 2021-12-02
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 1.0.7

import os

#####################################################################
# pcall@Version : 0.2.1
#####################################################################
import subprocess

if hasattr(subprocess, 'run'):
    __PY_VERSION_MINOR = 5  # 高于3.5
# except AttributeError:
else:
    __PY_VERSION_MINOR = 4  # 低于3.4

def _popen(str_cmd):
    completing_process = subprocess.Popen(str_cmd,
                                shell=True,
                                # stdin=subprocess.DEVNULL,
                                # stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
    # stdout, stderr = completing_process.communicate()
    return completing_process


def pcall(str_cmd, block=True):
    ''' return a list stdout-lines '''
    if block:
        if __PY_VERSION_MINOR == 5:
            p = subprocess.run(str_cmd,
                                shell=True,
                                check=True,
                                stdout=subprocess.PIPE)
        else:
            p = subprocess.check_call(str_cmd,
                                shell=True)
        stdout = p.stdout
    else:
        p = _popen(str_cmd)
        stdout = p.communicate()  # timeout=timeout
    # rc = p.returncode
    return stdout.decode().splitlines()

#####################################################################
# end of pcall
#####################################################################

class GitMixedStatus(Exception):
    """ Git status 状态不纯净（例如AM，即add了新文件，
        又进行了修改，但修改未添加到stage） """

class GitRepo:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    # def switch_dir(func):
    #     """ 装饰器 """
    #     def wrapper(self, args):
    #         print(args)
    #         cwd = os.path.abspath(os.path.curdir)
    #         os.chdir(self.repo_dir)
    #         ret = func(args)
    #         os.chdir(cwd)
    #         return ret
    #     return wrapper

    def switch_dir(func):
        """ 装饰器 """
        def wrapper(self, *args, **kwargs):
            def inner_wrapper():
                cwd = os.path.abspath(os.path.curdir)
                os.chdir(self.repo_dir)
                ret = func(self, *args, **kwargs)
                os.chdir(cwd)
                return ret
            return inner_wrapper()
        return wrapper

    @switch_dir
    def status(self, type_=None):
        list_lines = pcall("git status -s")
        if type_:
            list_lines = self._filter_status(list_lines, type_)

        # list_lines = [os.path.join(self.repo_dir, i) for i in list_lines]
        return list_lines

    def _filter_status(self, stdout_lines, type_):
        """ git-status是用两位状态表示的 """
        list_files = []
        for line in stdout_lines:
            _state, path_file = line.split(maxsplit=1)
            state_mixed = line[:2]

            path_file = path_file.strip('"')  # 去除对路径的双引号
            checking = {
                "untracked"         : state_mixed == "??",
                "added"             : state_mixed[0] != " ",
                "unadded"           : state_mixed[1] != " ",  # AM, MM, AD
                "new_added"         : state_mixed[0] == "A",  # A_
                "new_unadded"       : state_mixed[1] == "A",  # A_
                "modified_added"    : state_mixed[0] == "M",
                "modified_unadded"  : state_mixed[1] == "M",  # MM, AM, _M
                "deleted_added"     : state_mixed[0] == "D",
                "deleted_unadded"   : state_mixed[1] == "D",
                "rename_added"      : state_mixed[0] == "R",
                "rename_unadded"    : state_mixed[1] == "R",
            }[type_]
            if checking:
                list_files.append(path_file)

        return list_files

    def get_repo_relpath(self, path_abs):
        if path_abs.find(self.repo_dir) >= 0:
            path_rel = path_abs.split(self.repo_dir, 1)[1]
            return path_rel.strip("/").strip("\\")
        else:
            return path_abs

    @switch_dir
    def add(self, list_path):
        if isinstance(list_path, str):
            list_path = [list_path]
        list_path_rel = [self.get_repo_relpath(p) for p in list_path]
        pcall('git add "' + '" "'.join(list_path_rel) + '"')

    @switch_dir
    def reset(self, list_path):
        if isinstance(list_path, str):
            list_path = [list_path]
        list_path_rel = [self.get_repo_relpath(p) for p in list_path]
        pcall('git reset "' + '" "'.join(list_path_rel) + '"')

    @switch_dir
    def commit(self, message=None):
        if not message:
            from datetime import datetime
            message = datetime.now().strftime('%a, %b %d %H:%M')
        pcall(f'git commit -m "{message}"')

    @switch_dir
    def is_status_mixed(self):
        list_lines = pcall("git status -s")
        for line in list_lines:
            # _state = line.split(maxsplit=1)[0]
            _state = line[:2].strip()
            if _state != "??" and len(_state) != 1:
                return True

    @switch_dir
    def files(self, filter_ext=None):
        str_cmd = "git rev-list --objects --all | awk '{print $2}'"
        if filter_ext:
            str_cmd += f" | grep '{filter_ext}'"
        list_lines = pcall(str_cmd)
        return list_lines


if __name__ == "__main__":
    def test():
        git = GitRepo("./note/")
        list_files = git.files("\.md")
        # print(len(list_files))
        print(list_files)

    test()
