#!/usr/bin/env python3
# @Date    : 2021-12-03
# @Author  : Bright (brt2@qq.com)
# @Link    : https://gitee.com/brt2

import sqlite3

class ArticlesDB:
    tb_name = "essay"  # "articles"

    def __init__(self, path_db):
        self.db_connect(path_db)
        self.create_table()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def execute_scripts(self, SQL):
        print(f"SQL:\n\t{SQL}")
        self.cursor.execute(SQL)
        self.conn.commit()

    def db_connect(self, path_db=":memory"):
        print(">>>", path_db)
        self.conn = sqlite3.connect(path_db)  # 若不存在，则创建新数据库
        self.cursor = self.conn.cursor()  # database cursor

    def drop_table(self):
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.tb_name}; ")

    def create_table(self):
        SQL = """
        CREATE TABLE IF NOT EXISTS {} (
            filepath CHAR(200) NOT NULL PRIMARY KEY
            , postid CHAR(24) NOT NULL
            , title CHAR(100) NOT NULL
            , mdate CHAR(11)
            , tags TEXT
            , weight INTEGER default 5
            , UNIQUE (postid)
        ); """.format(self.tb_name)
        self.cursor.executescript(SQL)

    def del_item(self, path=None, postid=None):
        if path:
            SQL = f"DELETE FROM {self.tb_name} WHERE filepath='{path}'; "
        elif postid:
            SQL = f"DELETE FROM {self.tb_name} WHERE postid='{postid}'; "
        self.execute_scripts(SQL)

    def insert_item(self, path_file, postid, title, mdate, tags: list, weight=5):
        if weight is None:
            weight = 5
        SQL = f"INSERT INTO {self.tb_name} VALUES ('{path_file}', '{postid}', '{title}', '{mdate}', \"{tags}\", {weight}); "
        self.execute_scripts(SQL)

    def update_item(self, path_file, postid, title, mdate, tags: list, weight=5):
        # SQL = f"UPDATE {} SET {}='{}' WHERE md5='{}'; "
        self.del_item(path=path_file)
        self.insert_item(path_file, postid, title, mdate, tags, weight)

    def select(self):
        SQL = f"SELECT * FROM {self.tb_name}; "
        tuple_item = self.cursor.execute(SQL).fetchall()
        return tuple_item

    def get_postid(self, path):
        SQL = f"select postid from {self.tb_name} where filepath == '{path}'; "
        tuple_item = self.cursor.execute(SQL).fetchall()
        if tuple_item:
            return tuple_item[0][0]

    def update_filepath(self, path_from, path_to):
        SQL = f"UPDATE {self.tb_name} SET filepath='{path_to}' WHERE filepath ='{path_from}'; "
        self.execute_scripts(SQL)


def yaml2db(path_yaml="database.yml", path_db="test.db"):
    import yaml

    with open(path_yaml, "r", encoding="utf8") as fp:
        # self.data = json.load(fp)
        data = yaml.unsafe_load(fp)

    db = CnblogDB(path_db)

    def get_items(dict_, prefix):
        for subdir, subdict in dict_.items():
            prefix_next = prefix + [subdir]
            if "title" in subdict:
                path = "/".join(prefix_next)
                db.insert_item(path, subdict.get("postid"), subdict.get("title"),
                    subdict.get("date"), subdict.get("tags"), subdict.get("weight"))
            else:
                get_items(subdict, prefix_next)

    get_items(data["structure"]["programming"], [])
    print("Done")

if __name__ == "__main__":
    db = ArticlesDB("./test.db")
    postid = db.get_postid("1-os管理/11-linux/cmus.md")
    print(">>>", postid)
