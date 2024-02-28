from lib.db import db


class UsersShort:
    @staticmethod
    def run(handle):
        sql = db.template("users", "short")
        results = db.query_object_json(sql, {"handle": handle})
        return results
