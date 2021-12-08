#!/usr/bin/env python
# @Date    : 2021-12-03
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 0.2.1

import json
import platform
import os.path
import shutil

from util.gitsh import GitRepo

def getopt():
    import argparse

    parser = argparse.ArgumentParser("upload_cnblog", description="")
    parser.add_argument("-c", "--commit", action="store_true", help="提交文章")
    parser.add_argument("-p", "--push", action="store_true", help="推送至CnBlog博客园")
    parser.add_argument("-d", "--html2md", action="store_true", help="爬取html为markdown")
    return parser.parse_args()

class NoteRepoMgr:
    list_status = ["modified_added", "deleted_added", "new_added", "rename_added"]

    def __init__(self, cnblog):
        self.cnblog_mgr = cnblog
        dir_blog = cnblog.get_blogdir()
        self.path_cache = os.path.join(dir_blog,
                                       cnblog.get_cachapath())
        self.path_db = os.path.join(dir_blog, cnblog.get_dbpath())
        self.git = GitRepo(dir_blog)


    def commit_repo(self):
        if self.git.is_status_mixed():
            print("当前Stage暂存区有文件未更新至最新状态，无法判定用户明确的上传意图，请更新Repo仓库Git状态")
            return

        self.update_cache()
        self.git.add(self.path_cache)

        # git commit, 若无需提交，则Ctrl+C终止程序即可
        # commit_message = "更新programming"
        commit_message = input("Input commit message [回车默认提交]: ")
        self.git.commit(commit_message)

    def push(self):
        commit_message = input("请确认当前仓库已经pull至最新版本 [Y/n]: ")
        if commit_message != "Y":
            return
        update_files = self.load_cache()
        # 读取
        mod_, del_, new_, mov_ = [set(i) for i in update_files]
        for p in mod_ | new_:
            self.cnblog_mgr.post_blog(p)
        for p in del_:
            self.cnblog_mgr.delete_blog(p)
        for pfrom, pto in mov_:
            self.cnblog_mgr.move_blog(pfrom, pto)

        with open(self.path_cache, "w") as fp:
            json.dump([[]]*4, fp, ensure_ascii=False, indent=2)
        # 添加git add .cnblog.db

        self.git.add([self.path_cache, self.path_db])
        commit_message = "上传cnblogs"
        self.git.commit(commit_message)


    def load_cache(self):
        if os.path.exists(self.path_cache):
            with open(self.path_cache, "r") as fp:
                update_files = json.load(fp)
        else:
            update_files = [[] for i in range(len(self.list_status))]
        return update_files

    def save_cache(self, update_files):
        # 检查重复项
        print(update_files)
        # mod_, del_, new_ = [set(i) for i in update_files[:3]]
        ren_ = update_files[3]
        set_from, set_to = set(), set()
        for from_, to_ in ren_:
            set_from.add(from_)
            set_to.add(to_)
        list_items = [set(i) for i in update_files[:3]]
        list_items.extend([set_from, set_to])

        import itertools
        for a, b in itertools.permutations(list_items, 2):
            c = a & b
            assert not c, f"存在交叉文件:{c}"

        from pprint import pprint
        keys = ["修改项", "删除项", "增加项", "move_from", "move_to"]
        pprint(dict(zip(keys, list_items)))
        commit_message = input("确认是否保存上传 [<y>/n]: ")
        if commit_message != "y":
            raise AssertionError("终止执行")

        with open(self.path_cache, "w") as fp:
            json.dump(update_files, fp, ensure_ascii=False, indent=2)

    def update_cache(self):
        update_files = self.load_cache()
        for idx, status in enumerate(self.list_status):
            checked_files = update_files[idx]

            list_files = self.git.status(status)
            for path_file in list_files:
                isRename = status.startswith("rename")
                if isRename:
                    path_file, path_to = path_file.split(" -> ")

                if not path_file.endswith(".md"):
                    continue

                # moved??
                if isRename:
                    def move_cache(status: str):
                        idx = self.list_status.index(status)
                        if path_file in update_files[idx]:
                            update_files[idx].remove(path_file)
                            update_files[idx].append(path_to)
                            return True

                    if move_cache("modified_added"): continue
                    if move_cache("new_added"): continue
                    checked_files.append((path_file, path_to))

                elif path_file not in checked_files:
                    checked_files.append(path_file)
            # update_files.append(checked_files)

        self.save_cache(update_files)

def html2markdown(url, save_dir):
    j = urllib.urlopen(url)
    data_body = j.read()
    data_utf8 = data_body.decode("utf-8")

    html_parser = html2md.HTML2Text()
    md = html_parser.handle(data_utf8)
    assert md, "解析错误，未转换成Markdown格式文本"

    title = data_utf8.split('<title')[1].split(">", 1)[1].split('</title>')[0]
    if title == "\n":
        title = "null"
    path_save = os.path.join(save_dir, title + ".md")
    with open(path_save, "w", encoding="utf8") as fp:
        fp.write(md)
    print(f"[+] 已存储Markdown至【{path_save}】")


if __name__ == "__main__":
    args = getopt()

    from cnblog import CnblogManager
    path_curr = os.path.abspath(__file__)
    path_cnblog_account = os.path.join(os.path.dirname(path_curr), ".cnblog.json")
    cnblog = CnblogManager(path_cnblog_account)
    mgr = NoteRepoMgr(cnblog)

    # 处理命令行参数
    if args.commit:
        mgr.commit_repo()
    elif args.push:
        mgr.push()
    elif args.html2md:
        import urllib.request as urllib
        from util import html2md

        path = input("请输入URL地址: ")
        tmp_dir = os.path.join(cnblog.get_blogdir(), "download")
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        html2markdown(path, tmp_dir)

