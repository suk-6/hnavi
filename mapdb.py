import os
import os.path as osp
import sqlite3


class db:
    def __init__(self, dbname) -> None:
        self.root = osp.dirname(osp.abspath(__file__))
        self.dbname = f"{dbname}.sqlite"
        self.db = osp.join(self.root, "db", self.dbname)
        self.conn = self.getConnection(self.db)
        self.cur = self.conn.cursor()

    def initDB(self):
        self.cur.execute(
            """
            CREATE TABLE juso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ccd INTEGER,
                base_sn INTEGER,
                baseno_main INTEGER,
                baseno_sub INTEGER,                        
                roadseg_sn INTEGER,
                state TEXT,
                city TEXT,
                region_cd TEXT,
                region TEXT,
                road_cd TEXT,
                road TEXT,
                roadseg_start TEXT,
                roadseg_end TEXT,
                center_x TEXT,
                center_y TEXT,
                move_reason TEXT,
                change_date TEXT,
                effective_date TEXT
            )
            """
        )
        self.conn.commit()

    def getConnection(self, dbpath):
        if not osp.isdir(osp.join(self.root, "db")):
            os.makedirs(osp.join(self.root, "db"))

        return sqlite3.connect(dbpath, check_same_thread=False)

    def insertData(self, data):
        data = tuple(data)
        try:
            self.cur.execute(
                """
                INSERT INTO juso (
                    ccd,
                    base_sn,
                    baseno_main,
                    baseno_sub,
                    roadseg_sn,
                    state,
                    city,
                    region_cd,
                    region,
                    road_cd,
                    road,
                    roadseg_start,
                    roadseg_end,
                    center_x,
                    center_y,
                    move_reason,
                    change_date,
                    effective_date
                    ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )
                """,
                data,
            )
            self.conn.commit()
        except Exception as e:
            print(data)
            raise e

    def getDataOfID(self, id):
        self.cur.execute(f"SELECT * FROM juso WHERE id=?", (id,))
        return self.cur.fetchone()

    def getPositions(self):
        self.cur.execute(f"SELECT id, center_x, center_y FROM juso")
        return self.cur.fetchall()

    def getAll(self):
        self.cur.execute(f"SELECT * FROM juso")
        return self.cur.fetchall()


if __name__ == "__main__":
    dbconn = db("seoul")
    for data in dbconn.getAll():
        if data[11] == "마조로":
            print(data)
