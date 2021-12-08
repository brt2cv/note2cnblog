#!/usr/bin/env python3
# @Date    : 2021-11-22
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 0.1.3

import os.path
import re


class NullMarkdownFile(Exception):
    """ 空文件 """

class TextLocked(Exception):
    """ 文本内容已加锁，当前不可修改 """

# class MetaDataMissing(Exception):
#     """ 缺失元数据 """

# class TOC_Missing(Exception):
#     """ 缺失[TOC]标识 """


class MarkdownParser:
    """ 支持以下两种格式：
        1. 含H1格式的原生md文件（mkdocs）
        2. title = "xxx"... 定义元数据的hugo格式
    """
    pattern_images = {
        "all":  re.compile(r"!\[.*\]\((.*)\)"),
        "png":  re.compile(r"!\[.*\]\((.*\.png)\)"),
        "jpg":  re.compile(r"!\[.*\]\((.*\.jpg)\)"),
        "http": re.compile(r"!\[.*\]\((http.*?)\)"),
        "backup": re.compile(r"!\[.*\]\(.*\)\s*<!-- (.*) -->")
    }

    def __init__(self):
        self.ignore_websites = []

    def _clear_metadata(self):
        self.file_path = ""
        self.__text_lines = []
        self.__text_lock = False
        self.metadata = {
            "title": "",
            "description": "",
            "date": None,
            "weight": 5,
            "tags": [],
            "categories": [],
            "keywords": []
        }
        self.check_list = {
            "index_H1": None,
            "index_H2": None,
            "find_TOC": False,
        }

    def set_ignore_websites(self, list_ignore):
        self.ignore_websites = list_ignore

    def get_title(self):
        return self.metadata["title"] or self.metadata["description"]

    def get_weight(self):
        return self.metadata["weight"]

    def get_text(self):
        return self.__text_lines

    def set_text(self, list_lines):
        self.__text_lines = list_lines

    def _set_line(self, content):
        if not content.endswith("\n"):
            content += "\n"
        return content

    def modify_text(self, index, content):
        self.check_lock()
        self.__text_lines[index] = self._set_line(content)

    def insert_text(self, index, content):
        self.check_lock()
        self.__text_lines.insert(index, self._set_line(content))

    def append_text(self, content):
        self.check_lock()
        self.__text_lines.append(self._set_line(content))

    def pop_text(self, index):
        self.check_lock()
        self.__text_lines.pop(index)

    def lock_text(self):
        self.__text_lock = True

    def unlock_text(self):
        self.__text_lock = False

    def check_lock(self):
        if self.__text_lock:
            raise TextLocked()

    def load_file(self, path_file):
        self._clear_metadata()
        self.file_path = path_file
        with open(self.file_path, "r", encoding="utf8") as fp:
            self.__text_lines = fp.readlines()

        if not self.get_text():
            raise NullMarkdownFile()

        self._parse_metadata()

    def _parse_metadata(self):
        self.meta_range = [None, None]

        edit_meta = False
        for index, line in enumerate(self.get_text()):
            if edit_meta:
                if line.startswith("+++ -->"):
                    edit_meta = False
                    self.meta_range[1] = index
                else:
                    key, value = line.split("=")
                    self.metadata[key.strip()] = eval(value)
                continue

            if line.startswith("+++"):
                edit_meta = True
                self.meta_range[0] = index -1
                # self.check_list["has_metadata"] = True
            elif line.startswith("## "):
                self.check_list["index_H2"] = index
                # H2_text = line[2:].lstrip()
                # self.check_list["has_serial_num"] = H2_text.startswith("1. ")
                break
            elif line.startswith("# "):  # H1
                if not self.metadata["title"]:
                    self.metadata["title"] = line[2:].strip()
                self.check_list["index_H1"] = index
            elif line.startswith("[TOC]"):
                self.check_list["find_TOC"] = True

    def get_images(self, type_="all", force_abspath=True, ignore_websites=None):
        """ 临时有效，会加锁文本数据
            type_ in ("all", "local", "png", "jpg", "http", "backup")
            对于个人博客的地址前缀，不再重复下载图像
            https://img2020.cnblogs.com/blog/2039866/...
        """
        if ignore_websites is None:
            ignore_websites = []

        self.lock_text()

        is_type_local = type_ != "http"
        if type_ == "all":
            is_type_local = True
        if type_ == "local":
            type_ = "all"

        def match_regex(pattern, text):
            """ 适用于一个group的正则式 """
            re_match = re.match(pattern, text.strip())
            return re_match.group(1) if re_match else None

        dict_images = {}  # line: url
        for index, line in enumerate(self.get_text()):
            url_img = match_regex(self.pattern_images[type_], line)
            if url_img:
                if url_img.startswith("http"):
                    if is_type_local:
                        continue
                    elif line.find("<!--"):
                        be_ignored = False
                        for http_prefix in ignore_websites + self.ignore_websites:
                            if url_img.find(http_prefix) >= 0:
                                be_ignored = True
                                break
                        if be_ignored:
                            continue
                elif force_abspath and not os.path.isabs(url_img):  # 相对路径转换
                    url_img = os.path.join(os.path.dirname(self.file_path), url_img)
                dict_images[index] = url_img
        return dict_images

    def process_images(self, dict_images, callback):
        """ callback(url) -> new_url
        """
        self.unlock_text()
        for line_idx, url_img in dict_images.items():
            url_new = callback(url_img)
            if url_new:
                num_space = self.get_text()[line_idx].find("!")
                self.modify_text(line_idx, " "*num_space + "![]({})" % url_new)

    def make_title(self):
        blog_title = self.metadata["description"]  # 起一个吸引人的标题
        if blog_title:
            return blog_title

        filename_as_title = False
        blog_title = self.metadata["title"]
        file_name = os.path.basename(self.file_path)
        if not blog_title:
            blog_title = file_name[:-3]
            filename_as_title = True

        if file_name.startswith("simpread-"):
            if filename_as_title:
                blog_title = blog_title[len("simpread-"):]
            blog_title = "【转载】" + blog_title
        return blog_title

# if __name__ == "__main__":
#     import pathlib
#
#     parser = MarkdownParser()
#     path_md = pathlib.Path(r"D:\Home\workspace\note\programming\test\摄影入门.md")
#     parser.load_file(path_md)
#     dict_img = parser.get_images("local", force_abspath=False)
#     print(dict_img)
